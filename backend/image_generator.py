# generate_images_pw.py — auto-perfis pelos arquivos de sugestão
from tqdm import tqdm
import json
import asyncio
import base64
import random
import time
from pathlib import Path
from typing import List, Dict
from playwright.async_api import async_playwright, TimeoutError as PWTimeout
from collections import defaultdict
from support_scripts.alerts import ring_bell
from profiles import list_profiles, resolve_user_data_dir
from support_scripts.paths import MANIFEST_PATH, IMG_SUGGESTIONS_DIR, IMG_OUTPUT_DIR
from support_scripts.manifesto import load_manifest, save_manifest
import sys

# ====== PASTAS / CONSTANTES ======
ROOT = Path(__file__).resolve().parent
PROFILE_FOLDER = ROOT / "chrome_profiles"
SUGGESTIONS_DIR = IMG_SUGGESTIONS_DIR
IMG_OUT_DIR = IMG_OUTPUT_DIR
PROMPTS_DIR = ROOT.parent / "prompts"
IMG_PATTERNS_FILE = PROMPTS_DIR / "IMG_PATTERNS.txt"

IMAGEFX_URL = "https://labs.google/fx/tools/image-fx"
ALL_SUFFIXES = ["_01", "_02", "_03", "_04"]
SUFFIXES = ALL_SUFFIXES[:1]

def load_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()

def load_img_patterns():
    """
    Parse IMG_PATTERNS.txt containing entries in the form 'alias;description'.
    Allows multi-line descriptions by treating subsequent lines as part of the current alias.
    """
    if not IMG_PATTERNS_FILE.exists():
        return []
    lines = IMG_PATTERNS_FILE.read_text(encoding="utf-8").splitlines()
    patterns = []
    current_alias = None
    current_desc: list[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        lowered = line.lower()
        if lowered.startswith("pattern") and lowered.endswith(":"):
            continue
        if ";" in line:
            alias_part, desc_part = line.split(";", 1)
            alias = alias_part.strip()
            desc = desc_part.strip()
            if alias and desc:
                if current_alias:
                    patterns.append((current_alias, " ".join(current_desc).strip()))
                current_alias = alias
                current_desc = [desc]
                continue
        if current_alias:
            current_desc.append(line)
    if current_alias:
        patterns.append((current_alias, " ".join(current_desc).strip()))
    return patterns


def select_pattern_text() -> str:
    entries = load_img_patterns()
    if not entries:
        print("⚠️ No entries found in IMG_PATTERNS.txt.")
        return ""

    print("\n🎨 Available Patterns:")
    for idx, (alias, desc) in enumerate(entries, 1):
        preview = desc.split(".")[0][:80]
        suffix = "..." if len(desc) > len(preview) else ""
        print(f"{idx}. {alias} — {preview}{suffix}")

    prompt = f"➡️ Choose pattern (1-{len(entries)} | default 1): "
    raw = input(prompt).strip()
    try:
        choice = int(raw or "1")
    except Exception:
        choice = 1
    choice = max(1, min(len(entries), choice))
    alias, desc = entries[choice - 1]
    print(f"🎯 Selected: {alias}")
    return desc

ALL_ERRORS = defaultdict(lambda: {"total": 0, "cenas": []})

def report_errors(base: str):
    total = sum(data["total"] for data in ALL_ERRORS.values())
    if total == 0:
        return
    print(f"\n⚠️ {base}: {total} failure(s) generating images.")
    for profile, data in ALL_ERRORS.items():
        if data["total"]:
            sample = ", ".join(data["cenas"][:5])
            suffix = "..." if len(data["cenas"]) > 5 else ""
            print(f"   • Profile {profile}: {data['total']} scenes (e.g.: {sample}{suffix})")
    ALL_ERRORS.clear()


def set_images_status(mf: dict, base: str, status: str, images_saved: int | None = None):
    entry = mf.setdefault(base, {})
    entry["images"] = status
    if images_saved is not None:
        entry["images_saved"] = images_saved
    entry["last_update"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    save_manifest(mf)


async def ask_retry_decision(base: str, profile: str, failed_ids: list[int]) -> bool:
    sample = ", ".join(f"{sid:03}" for sid in failed_ids[:5])
    suffix = "..." if len(failed_ids) > 5 else ""
    print(f"⚠️ {base}/{profile}: {len(failed_ids)} scenes failed (e.g.: {sample}{suffix}). Retrying automatically.")
    return True

# ==========================
# PROMPTS / SUGESTÕES
# ==========================


def parse_profile_suggestions(base: str) -> Dict[str, Dict[int, str]]:
    base_dir = SUGGESTIONS_DIR / base
    if not base_dir.exists():
        return {}

    result: Dict[str, Dict[int, str]] = {}
    for txt in sorted(base_dir.glob(f"{base}__*.txt")):
        name = txt.stem
        if "__" not in name:
            continue
        perfil = name.split("__", 1)[1]
        scene_map: Dict[int, str] = {}
        lines = txt.read_text(encoding="utf-8").splitlines()
        current_scene = None
        for line in lines:
            if line.startswith("Scene "):
                parts = line.split()
                if len(parts) >= 2 and parts[1].isdigit():
                    current_scene = int(parts[1])
                else:
                    current_scene = None
            elif line.startswith("Suggestion:"):
                if current_scene is not None:
                    prompt = line.split("Suggestion:", 1)[1].strip()
                    scene_map[current_scene] = prompt
                    current_scene = None
        if scene_map:
            result[perfil] = scene_map
    return result


def list_pending_bases_from_manifest() -> List[str]:
    mf = load_manifest()
    pending_bases = [b for b, info in mf.items() if info.get("suggestions") == 'done' and info.get("images") != 'done']

    for subdir in SUGGESTIONS_DIR.iterdir():
        if subdir.is_dir() and subdir.name not in mf:
            pending_bases.append(subdir.name)

    seen, unique = set(), []
    for b in pending_bases:
        if b not in seen:
            seen.add(b)
            unique.append(b)
    return unique

# ==========================
# DISCO (imagens salvas)
# ==========================


def expected_scene_paths(base: str, idx: int) -> list[Path]:
    scene = f"{idx:03}"
    root = IMG_OUT_DIR / base
    return [(root / suffix / f"{scene}.jpg") for suffix in SUFFIXES]


def is_scene_complete(base: str, idx: int) -> bool:
    return all(p.exists() for p in expected_scene_paths(base, idx))


def save_scene_images(base: str, scene_idx: int, b64_list: List[str]) -> int:
    scene = f"{scene_idx:03}"
    out_root = IMG_OUT_DIR / base
    out_root.mkdir(parents=True, exist_ok=True)
    saved = 0
    odd_positions = [i for i in range(1, len(b64_list) + 1, 2)]
    for pos_idx, pos in enumerate(odd_positions[:len(SUFFIXES)], start=0):
        suffix = SUFFIXES[pos_idx]
        folder = out_root / suffix
        folder.mkdir(parents=True, exist_ok=True)
        b64 = b64_list[pos - 1]
        try:
            (folder / f"{scene}.jpg").write_bytes(base64.b64decode(b64))
            saved += 1
        except Exception as e:
            print(f"⚠️ Failed to save {scene}.jpg in {suffix}: {e}")
    return saved

# ==========================
# PLAYWRIGHT HELPERS
# ==========================


async def ensure_editor_ready(page):
    try:
        container = page.locator("div.sc-1004f4bc-4.fZKmcZ").first
        await container.wait_for(timeout=10000)
        await container.click()
        await container.click()
    except PWTimeout:
        pass
    textbox = page.locator("div[role='textbox'][contenteditable='true']").first
    await textbox.wait_for(timeout=15000)
    await textbox.click()
    await asyncio.sleep(0.25)
    await textbox.click()
    await asyncio.sleep(0.15)
    return textbox


async def move_caret_to_end(page):
    try:
        await page.keyboard.press("Control+End")
        await asyncio.sleep(0.05)
    except Exception:
        pass


async def send_prompt_and_collect(page, prompt_text: str, timeout_ms=90000) -> List[str]:
    await move_caret_to_end(page)
    await page.keyboard.insert_text(pattern + prompt_text)
    await asyncio.sleep(random.uniform(0.6, 1.6))
    await page.keyboard.press("Enter")

    imgs = page.locator("img[src^='data:image']")
    await imgs.first.wait_for(timeout=timeout_ms)
    b64_list = []
    count = await imgs.count()
    for i in range(count):
        src = await imgs.nth(i).get_attribute("src")
        if src and "," in src:
            b64_list.append(src.split(",", 1)[1])

    await page.keyboard.press("Control+A")
    await asyncio.sleep(0.15)
    await page.keyboard.press("Backspace")
    await asyncio.sleep(0.15)

    return b64_list

# ==========================
# WORKER
# ==========================


async def worker_task(worker_id: int, context, base: str, profile: str,
                      scene_map: Dict[int, str], q: asyncio.Queue, pbar,
                      failures: list[int]):
    page = await context.new_page()
    await page.goto(IMAGEFX_URL, wait_until="domcontentloaded")
    await ensure_editor_ready(page)

    while True:
        idx = await q.get()
        if idx is None:
            q.task_done()
            break
        try:
            prompt = scene_map[idx]
            b64_list = await send_prompt_and_collect(page, prompt, timeout_ms=90000)
            if b64_list:
                save_scene_images(base, idx, b64_list)
                # direct manifest update — no lock
                mf = load_manifest()
                current = int(mf.get(base, {}).get("images_saved") or 0)
                set_images_status(mf, base, "in_progress", images_saved=max(current, idx))
            pbar.update(1)
            # Send JSON progress to frontend
            try:
                prog_json = json.dumps({
                    "type": "progress",
                    "profile": profile,
                    "current": pbar.n,
                    "total": pbar.total,
                    "percentage": (pbar.n / pbar.total * 100) if pbar.total else 0
                })
                # Print with custom tags to ensure reliable parsing
                sys.stdout.write(f"\n<<PROGRESS>>{prog_json}<<PROGRESS>>\n")
                sys.stdout.flush()
            except Exception:
                pass
        except Exception as e:
            ALL_ERRORS[profile]["total"] += 1
            ALL_ERRORS[profile]["cenas"].append(f"{idx:03}")
            failures.append(idx)
        finally:
            q.task_done()
    await page.close()


async def execute_scene_batch(base: str,
                              profile: str,
                              ctx,
                              scene_map: Dict[int, str],
                              scene_ids: list[int],
                              workers_per_profile: int,
                              position: int,
                              desc_suffix: str) -> list[int]:
    if not scene_ids:
        return []

    q: asyncio.Queue = asyncio.Queue()
    for sid in scene_ids:
        q.put_nowait(sid)

    pbar = tqdm(
        total=len(scene_ids),
        desc=desc_suffix,
        leave=True,
        file=sys.stdout,
        ncols=80,
        mininterval=0.5,
        ascii=True,
        disable=False,
        bar_format="{desc}: {percentage:3.0f}%|{bar}| {n_fmt}/{total_fmt}"
    )

    failures: list[int] = []
    workers = [
        asyncio.create_task(
            worker_task(wid, ctx, base, profile, scene_map, q, pbar, failures)
        )
        for wid in range(1, max(1, workers_per_profile) + 1)
    ]

    await q.join()
    for _ in workers:
        q.put_nowait(None)

    await asyncio.gather(*workers, return_exceptions=True)

    try:
        pbar.close()
    except Exception:
        pass

    return failures

async def process_profile(base: str,
                          profile: str,
                          ctx,
                          scene_map: Dict[int, str],
                          pendentes: list[int],
                          workers_per_profile: int,
                          position: int,
                          desc_suffix: str | None = None) -> list[int]:
    desc = desc_suffix or f"{base} / {profile}"
    await execute_scene_batch(
        base, profile, ctx, scene_map, pendentes, workers_per_profile, position, desc
    )
    return [sid for sid in pendentes if not is_scene_complete(base, sid)]


# ==========================
# EXECUÇÃO POR BASE
# ==========================

async def run_for_base_with_profiles(pw, base: str, workers_per_profile: int, headless: bool):
    profile_contexts = {}
    scene_maps = {}
    ordered_profiles: list[str] = []
    try:
        per_profile_scenes = parse_profile_suggestions(base)
        if not per_profile_scenes:
            print(f"⚠️ {base}: did not find '<base>__<profile>.txt' files in {SUGGESTIONS_DIR/base}")
            return

        available_profiles = set(list_profiles())
        chosen = [(p, scene_map) for p, scene_map in per_profile_scenes.items() if p in available_profiles]
        missing = [p for p in per_profile_scenes.keys() if p not in available_profiles]
        if missing:
            print(f"⚠️ Non-existent profiles (ignoring): {missing}")
        if not chosen:
            print(f"❌ No valid profile found for {base}.")
            return

        pending_chosen = []
        for profile, scene_map in chosen:
            scene_ids = sorted(scene_map.keys())
            tem_pendencia = any(not is_scene_complete(base, sid) for sid in scene_ids)
            if tem_pendencia:
                pending_chosen.append((profile, scene_map))
            else:
                print(f"✅ {base} / profile '{profile}': already completed, will not be opened.")

        if not pending_chosen:
            mf_final = load_manifest()
            all_scene_ids = sorted({sid for _, m in chosen for sid in m.keys()})
            total = max(all_scene_ids) if all_scene_ids else 0
            set_images_status(mf_final, base, "done", images_saved=total)
            print(f"🏁 {base}: nothing pending in any profile. Marked as done.")
            return

        mf = load_manifest()
        if base not in mf:
            mf[base] = {"images": "in_progress", "images_saved": 0}
            save_manifest(mf)
        elif mf[base].get("images") not in ("pending", "in_progress"):
            mf[base]["images"] = "in_progress"
            save_manifest(mf)

        # === STEP 1: open only profiles with pending items ===
        for idx, (profile, scene_map) in enumerate(pending_chosen):
            user_data_dir = resolve_user_data_dir(profile)
            ctx = await pw.chromium.launch_persistent_context(
                user_data_dir=str(user_data_dir),
                headless=headless,
                channel="chrome",
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-first-run",
                    "--no-default-browser-check",
                    "--disable-infobars",
                ],
            )
            await ctx.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                if (!window.chrome) window.chrome = { runtime: {} };
            """)
            profile_contexts[profile] = ctx
            scene_maps[profile] = scene_map
            ordered_profiles.append(profile)
            if idx < len(pending_chosen) - 1:
                await asyncio.sleep(1.0)

        # === STEP 2: print pending items ===
        print("\n")
        print("=" * 60)
        print(f"🎬 PENDING SCENES SUMMARY\n")
        all_pendentes = {}

        for profile in ordered_profiles:
            scene_map = scene_maps[profile]
            scene_ids = sorted(scene_map.keys())
            pendentes = [sid for sid in scene_ids if not is_scene_complete(base, sid)]
            if pendentes:
                all_pendentes[profile] = pendentes
                print(f"🎯 {base} / profile '{profile}': {len(pendentes)} pending scenes "
                      f"(e.g.: {pendentes[:10]}{' ...' if len(pendentes)>10 else ''})")

        if not all_pendentes:
            print(f"✅ {base}: no profile with pending items.")
            return

        # === STEP 3: create progress ===
        print("\n## PROGRESS:")
        print("-" * 60)

        supervisors = []
        profile_positions = {}
        active_profiles = [p for p in ordered_profiles if p in all_pendentes]
        for position, profile in enumerate(active_profiles):
            ctx = profile_contexts[profile]
            scene_map = scene_maps[profile]
            pendentes = all_pendentes[profile]
            profile_positions[profile] = position
            supervisors.append((profile, asyncio.create_task(
                process_profile(base, profile, ctx, scene_map, pendentes, workers_per_profile, position)
            )))

        print("-" * 60)

        results = await asyncio.gather(
            *(task for _, task in supervisors),
            return_exceptions=True
        )

        remaining_by_profile: dict[str, list[int]] = {}
        for (profile, _), result in zip(supervisors, results):
            if isinstance(result, Exception):
                print(f"❌ {base} / {profile}: error during processing: {result}")
                remaining_by_profile[profile] = all_pendentes.get(profile, [])
            else:
                if result:
                    remaining_by_profile[profile] = result

        # === STEP 4: global retries ===
        retry_round = 1
        while remaining_by_profile:
            normalized = {}
            for profile, ids in remaining_by_profile.items():
                unresolved = [sid for sid in ids if not is_scene_complete(base, sid)]
                if unresolved:
                    normalized[profile] = unresolved
            if not normalized:
                break

            retry_requests = {}
            for profile, unresolved in normalized.items():
                wants_retry = await ask_retry_decision(base, profile, unresolved)
                if wants_retry:
                    retry_requests[profile] = unresolved
            if not retry_requests:
                break

            retry_tasks = []
            for profile, retry_ids in retry_requests.items():
                ctx = profile_contexts.get(profile)
                scene_map = scene_maps.get(profile)
                if ctx is None or scene_map is None:
                    continue
                position = profile_positions.get(profile, len(profile_positions))
                desc = f"{base} / {profile} (retry #{retry_round})"
                retry_tasks.append((profile, asyncio.create_task(
                    process_profile(base, profile, ctx, scene_map, retry_ids, workers_per_profile, position, desc)
                )))

            if not retry_tasks:
                break

            retry_results = await asyncio.gather(
                *(task for _, task in retry_tasks),
                return_exceptions=True
            )
            remaining_by_profile = {}
            for (profile, _), result in zip(retry_tasks, retry_results):
                if isinstance(result, Exception):
                    print(f"❌ {base} / {profile}: error during retry: {result}")
                    remaining_by_profile[profile] = normalized.get(profile, [])
                elif result:
                    remaining_by_profile[profile] = result
            retry_round += 1

        all_scene_ids = sorted({sid for _, m in chosen for sid in m.keys()})
        if not all_scene_ids:
            return
        total = max(all_scene_ids)
        restam = [sid for sid in all_scene_ids if not is_scene_complete(base, sid)]
        mf_final = load_manifest()
        if not restam:
            set_images_status(mf_final, base, "done", images_saved=total)
            print(f"\n🏁 Completed: {base} ({total}/{total})")
        else:
            maior = max([sid for sid in all_scene_ids if is_scene_complete(base, sid)], default=0)
            set_images_status(mf_final, base, "in_progress", images_saved=maior)
            print(f"\n⏸️ Partial: {base} (missing {len(restam)} scenes) — keeping 'in_progress'")
    finally:
        for ctx in profile_contexts.values():
            try:
                await ctx.close()
            except Exception:
                pass
        report_errors(base)

# ==========================
# MAIN
# ==========================


async def main():
    try:
        bases = list_pending_bases_from_manifest()
        if not bases:
            print("📭 No pending bases for images.")
            return

        print("\n🗂️ Available bases:")
        for i, b in enumerate(bases, 1):
            print(f"{i}. {b}")
        print("0. all")

        raw = input("➡️ Select (e.g. 2 3 or '0' for all): ").strip().lower()
        if raw in ("0", "all"):
            selected = bases
        else:
            try:
                idxs = [int(x) for x in raw.split()]
                selected = [bases[i-1] for i in idxs if 1 <= i <= len(bases)]
            except Exception:
                print("❌ Invalid input.")
                return
            if not selected:
                print("❌ Nothing selected.")
                return

        try:
            workers_per_profile = int(input("➡️ Tabs per profile? (suggestion 2): ").strip() or "2")
        except Exception:
            workers_per_profile = 2
        workers_per_profile = max(1, min(4, workers_per_profile))

        try:
            total_images_raw = input("➡️ Total images to download? (Max: 4 | Default: 1): ").strip()
            total_images = int(total_images_raw or "1")
        except Exception:
            total_images = 1
        total_images = max(1, min(len(ALL_SUFFIXES), total_images))
        global SUFFIXES, pattern
        SUFFIXES = ALL_SUFFIXES[:total_images]
        pattern = select_pattern_text()

        headless_raw = input("➡️ Run in headless mode? (ENTER = yes): ").strip().lower()
        headless = True
        if headless_raw in ("n", "no", "false", "0"):
            headless = False

        async with async_playwright() as pw:
            for base in selected:
                await run_for_base_with_profiles(pw, base, workers_per_profile, headless)
    finally:
        ring_bell("✅ Finished processing selected bases.")


if __name__ == "__main__":
    asyncio.run(main())
