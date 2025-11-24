"""Generate visual suggestions for processed TXT scripts."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

from support_scripts.alerts import ring_bell
from support_scripts.manifesto import ensure_entry, load_manifest, update_stage
from support_scripts.paths import IMG_SUGGESTIONS_DIR, TXT_PROCESSED_DIR
from profiles import choose_profiles, list_profiles

# ==========================
# CONFIG
# ==========================
ROOT = Path(__file__).resolve().parent
INPUT_DIR = TXT_PROCESSED_DIR
OUTPUT_DIR = IMG_SUGGESTIONS_DIR
PROMPT_PATH = "prompts/Scene_Suggestion.txt"

# ==========================
# ENV
# ==========================
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
print("Model set to:", OPENAI_MODEL)

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in .env")
client = OpenAI(api_key=OPENAI_API_KEY)


def load_text(path: str | Path) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read().strip()


def remove_txt_tags(text: str) -> str:
    """Remove any XML-like tags (e.g. <hook>, </problem>) from the text."""
    return re.sub(r'<[^>]+>', '', text)


def locate_processed_txt(base: str) -> Path | None:
    """
    Locate the processed TXT for a base.
    Priority is txt_processed/base/base.txt, falling back to txt_processed/base.txt,
    and finally any matching file in the tree.
    """
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    folder_candidate = INPUT_DIR / base / f"{base}.txt"
    if folder_candidate.exists():
        return folder_candidate

    top_level = INPUT_DIR / f"{base}.txt"
    if top_level.exists():
        return top_level

    matches = list(INPUT_DIR.rglob(f"{base}.txt"))
    return matches[0] if matches else None


def read_base_lines(base: str) -> tuple[list[str], Path | None]:
    """Read processed TXT lines for the base, stripping blanks. (Used in Per-Scene mode)"""
    txt_path = locate_processed_txt(base)
    if txt_path is None:
        return [], None
    
    # Read full content to clean tags first
    raw_content = txt_path.read_text(encoding="utf-8")
    cleaned_content = remove_txt_tags(raw_content)
    
    lines = [line.strip() for line in cleaned_content.splitlines() if line.strip()]
    return lines, txt_path


def split_into_sentences(text: str) -> list[str]:
    """Split raw text into sentences (Used in Global mode)"""
    if not text:
        return []
    cleaned = re.sub(r"\s+", " ", text.strip())
    sentences = re.split(r"(?<=[.?!])\s+", cleaned)
    result = [s.strip() for s in sentences if s.strip()]
    if not result and cleaned:
        result = [cleaned]
    return result


def read_processed_sentences(base: str) -> tuple[list[str], Path | None]:
    """Reads raw text, splits into sentences, and returns the list (Used in Global mode)"""
    txt_path = locate_processed_txt(base)
    if txt_path is None:
        return [], None
    raw_text = txt_path.read_text(encoding="utf-8").strip()
    raw_text = remove_txt_tags(raw_text)
    return split_into_sentences(raw_text), txt_path


def count_sentences_for_base(base: str) -> tuple[int | None, Path | None]:
    sentences, txt_path = read_processed_sentences(base)
    if txt_path is None:
        return None, None
    return len(sentences), txt_path


def group_lines(lines: list[str], group_size: int, joiner: str = "\n") -> list[str]:
    """
    Groups lines/sentences. Uses '\n' joiner for Per-Line mode (to keep lines separated
    for model context) or ' ' for Global mode sentences.
    """
    if group_size <= 1:
        return lines
    chunks = []
    for i in range(0, len(lines), group_size):
        chunk_lines = [line for line in lines[i : i + group_size] if line]
        if not chunk_lines:
            continue
        # CORRECTION: Uses 'joiner' to join lines (will be '\n' for Per-Scene mode)
        chunk = joiner.join(chunk_lines).strip()
        if chunk:
            chunks.append(chunk)
    return chunks


def ask_model(full_prompt: str, scene_text: str) -> str:
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": full_prompt},
            {"role": "user", "content": scene_text},
        ],
        temperature=0.7,
    )
    return resp.choices[0].message.content.strip()


def detect_completed_scenes(out_path: Path) -> int:
    if not out_path.exists():
        return 0
    count = 0
    with open(out_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Scene "):
                count += 1
    return count


def ensure_manifest_for_inbox() -> None:
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    for txt_file in INPUT_DIR.rglob("*.txt"):
        ensure_entry(txt_file.stem)


def parse_json_suggestions(raw: str) -> list[str]:
    """Attempts to parse JSON response from LLM."""
    cleaned = raw.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    suggestions: list[str] = []
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            data = data.get("suggestions")
        if isinstance(data, list):
            suggestions = [str(item).strip() for item in data if str(item).strip()]
            suggestions = [s if s.lower().startswith("show") else f"Show {s}" for s in suggestions]
            return suggestions
    except Exception:
        pass
    # Fallback for simple parsing (non-JSON list)
    for line in cleaned.splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0] in {"-", "•", "*"}:
            line = line[1:].strip()
        m = re.match(r"^(?:\d+[.)-]?\s*)(.*)$", line)
        if m:
            line = m.group(1).strip()
        if not line:
            continue
        if not line.lower().startswith("show"):
            line = f"Show {line}"
        suggestions.append(line.strip())
    return suggestions


def list_ready_for_suggestions() -> list[str]:
    mf = load_manifest()
    # Using 'txt' as done, as in your original simple code, for consistency.
    return [
        base
        for base, info in mf.items()
        if info.get("txt") == "done" and info.get("suggestions") != "done"
    ]


# ==========================
# GLOBAL MODE
# ==========================
def process_base_full_script(base: str, suggestion_count: int, chosen_profiles: list[str]) -> None:
    ensure_entry(base)
    base_out_dir = OUTPUT_DIR / base
    base_out_dir.mkdir(parents=True, exist_ok=True)

    update_stage(base, "suggestions", "in_progress")

    try:
        # Global Mode uses read_processed_sentences (splits into sentences)
        sentences, txt_path = read_processed_sentences(base)
        if txt_path is None:
            update_stage(base, "suggestions", "error: processed txt not found")
            return
        full_script = txt_path.read_text(encoding="utf-8").strip()
        if not full_script:
            update_stage(base, "suggestions", "error: empty processed txt")
            return

        prompt_core = load_text(PROMPT_PATH)
        full_prompt = (
            f"{prompt_core}\n\n"
            f"You receive the entire processed script. Craft {suggestion_count} distinct visual suggestions "
            f"inspired by the whole narrative. Respond ONLY with JSON using the schema: "
            f'{{"suggestions": ["Show ...", ...]}}. Keep them concise and literal.'
        )
        scene_text = (
            f"Base: {base}\n\n"
            f"FULL SCRIPT:\n{full_script}\n\n"
            f"Generate {suggestion_count} numbered image ideas capturing different striking moments or moods. "
            f"Each suggestion must start with 'Show...'."
        )
        response = ask_model(full_prompt, scene_text)
        suggestions = parse_json_suggestions(response)
        if not suggestions:
            update_stage(base, "suggestions", "error: model returned no suggestions")
            return
        
        # Logic for filling/cutting suggestions
        if len(suggestions) < suggestion_count:
            buffered = suggestions.copy()
            while len(suggestions) < suggestion_count:
                suggestions.extend(buffered)
            suggestions = suggestions[:suggestion_count]
        else:
            suggestions = suggestions[:suggestion_count]

        total = len(suggestions)
        P = max(1, len(chosen_profiles))
        base_chunk = total // P
        remainder = total % P
        scene_offset = 0

        # Division of suggestions among profiles
        for idx, prof_name in enumerate(chosen_profiles):
            share = base_chunk + (1 if idx < remainder else 0)
            if share <= 0:
                continue
            subset = suggestions[scene_offset : scene_offset + share]
            start_scene = scene_offset + 1
            end_scene = start_scene + len(subset) - 1
            desc = f"{base}__{prof_name} ({start_scene}-{end_scene})"
            out_path = base_out_dir / f"{base}__{prof_name}.txt"
            with open(out_path, "w", encoding="utf-8") as f_out:
                for offset, suggestion in enumerate(
                    tqdm(subset, desc=desc, total=len(subset), leave=False),
                    start=0,
                ):
                    scene_number = start_scene + offset
                    block = [
                        f"Scene {scene_number}",
                        f"Suggestion: {suggestion.strip()}",
                        "",
                    ]
                    f_out.write("\n".join(block) + "\n")
            scene_offset += share

        update_stage(
            base,
            "suggestions",
            "done",
            extra={
                "mode": "full_script",
                "total_suggestions": total,
                "requested_suggestions": suggestion_count,
                "scenes": total,
                "group_size": 1,
            },
        )
        print(f"[OK] {base} → {total} global suggestions completed.")

    except Exception as err:  # pragma: no cover - defensive
        update_stage(base, "suggestions", f"error: {err}")
        print(f"[ERRO] {base}: {err}")


# ==========================
# PER-LINE MODE (Per-Scene Mode - Corrected)
# ==========================
def process_base(
    base: str,
    group_size: int,
    chosen_profiles: list[str],
    target_suggestions: int | None = None,
) -> None:
    ensure_entry(base)
    base_out_dir = OUTPUT_DIR / base
    base_out_dir.mkdir(parents=True, exist_ok=True)

    # CORRECTION: Use line-by-line reading function (read_base_lines)
    txt_lines, txt_path = read_base_lines(base)

    if txt_path is None:
        update_stage(base, "suggestions", "error: processed txt not found")
        return

    update_stage(base, "suggestions", "in_progress")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        if not txt_lines:
            update_stage(base, "suggestions", "error: empty txt file")
            return

        prompt_core = load_text(PROMPT_PATH)
        # CORRECTION: Prompt with clear instruction to generate ONE suggestion per BLOCK (scene)
        full_prompt = (
            f"{prompt_core}\n\n"
            f"--- TEXT ---\n\n"
            f"Generate ONE concise visual suggestion for the following block of text, starting with 'Show...' and strictly adhering to all policies and formatting rules defined above."
        )

        # CORRECTION: Use '\n' as joiner to group lines, maintaining original structure
        scenes = group_lines(txt_lines, group_size, joiner="\n")
        total_available = len(scenes)
        if total_available == 0:
            update_stage(base, "suggestions", "error: no scenes after grouping")
            return
        
        # Logic for repeating/cutting scenes
        if target_suggestions and target_suggestions > 0:
            target = target_suggestions
        else:
            target = total_available
            
        if target <= total_available:
            scenes = scenes[:target]
        else:
            repeated: list[str] = []
            while len(repeated) < target:
                repeated.extend(scenes)
            scenes = repeated[:target]
        total = len(scenes)

        P = max(1, len(chosen_profiles))
        base_chunk = total // P
        remainder = total % P

        ranges = []
        if P == 1:
            ranges.append((1, total))
        else:
            first_count = base_chunk + remainder
            start = 1
            end = first_count
            ranges.append((start, end))
            for _ in range(1, P):
                start = end + 1
                end = start + base_chunk - 1
                ranges.append((start, end))

        for prof_name, (start_idx, end_idx) in zip(chosen_profiles, ranges):
            if start_idx > end_idx:
                continue

            out_path = base_out_dir / f"{base}__{prof_name}.txt"
            done_sub = detect_completed_scenes(out_path)
            mode = "a" if done_sub > 0 else "w"

            with open(out_path, mode, encoding="utf-8") as f_out:
                for j, scene_idx in enumerate(
                    tqdm(
                        range(start_idx, end_idx + 1),
                        desc=f"{base}__{prof_name} ({start_idx}-{end_idx})",
                        initial=done_sub,
                        total=(end_idx - start_idx + 1),
                    ),
                    start=1,
                ):
                    if j <= done_sub:
                        continue

                    scene_text = scenes[scene_idx - 1]
                    max_retries = 3
                    for attempt in range(1, max_retries + 1):
                        try:
                            suggestion = ask_model(full_prompt, scene_text)
                            if "[ERRO AO GERAR" in suggestion or "Request timed out" in suggestion:
                                raise RuntimeError("Model returned internal error")
                            final_suggestion = suggestion.strip()
                            break
                        except Exception as err:
                            if attempt < max_retries:
                                print(
                                    f"⚠️ Scene {scene_idx}: attempt {attempt}/{max_retries} failed ({err}), retrying..."
                                )
                                continue
                            else:
                                print(f"❌ Scene {scene_idx}: persistent error ({err})")
                                final_suggestion = f"[ERROR GENERATING: {err}]"

                    # CORRECTION: Writing block with "Original:" and single-line speeches
                    block = [
                        f"Scene {scene_idx}",
                        "Original:",
                        scene_text.replace("\n", " "), # Joins original lines (which came separated by \n)
                        f"Suggestion: {final_suggestion}",
                        ""
                    ]
                    f_out.write("\n".join(block) + "\n")
                    f_out.flush()

        extra_info = {"scenes": total, "group_size": group_size}
        if target_suggestions and target_suggestions > 0:
            extra_info["requested_suggestions"] = target_suggestions
        update_stage(base, "suggestions", "done", extra=extra_info)
        print(f"[OK] {base} → split among {len(chosen_profiles)} profile(s) (scenes: {total}, group={group_size})")

    except Exception as err:  # pragma: no cover - defensive
        update_stage(base, "suggestions", f"error: {str(err)}")
        print(f"❌ {base}: {err}")


# ==========================
# MAIN
# ==========================
def main() -> None:
    try:
        ensure_manifest_for_inbox()
        
        # Normal mode (existing code)
        args = [a for a in sys.argv[1:] if not a.startswith("-")]
        candidates = list_ready_for_suggestions()
        candidates = list_ready_for_suggestions()
        if not candidates:
            print("No files pending suggestions.")
            return

        if args:
            if "all" in [a.lower() for a in args]:
                selected = candidates
            else:
                selected = args
        else:
            print("\n📂 Available files:")
            for i, base in enumerate(candidates, 1):
                print(f"{i}. {base}")
            print("0. ALL")

            choice = input("➡️ Enter number(s) separated by commas or 0 for ALL: ").strip()
            if not choice:
                print("❌ No choice made.")
                return

            if choice == "0":
                selected = candidates
            else:
                try:
                    idxs = [int(x) for x in choice.split(",")]
                    selected = [candidates[i - 1] for i in idxs if 1 <= i <= len(candidates)]
                except Exception:
                    print("❌ Invalid input.")
                    return

        sentence_counts: dict[str, int | None] = {}
        total_sentences = 0
        print("\n📊 Sentences per file:")
        for base in selected:
            # Uses count_sentences_for_base, which uses sentence logic for initial count
            count, _ = count_sentences_for_base(base) 
            sentence_counts[base] = count
            if count is None:
                print(f" - {base}: Processed TXT not found")
            else:
                print(f" - {base}: {count} sentences")
                total_sentences += count
        if total_sentences == 0:
            print("⚠️ Could not count sentences in any valid file.")

        mode_raw = input("➡️ Mode? (1 = global suggestions, 2 = standard per speech | ENTER = 2): ").strip()
        use_global_mode = mode_raw == "1"
        group_size = 1
        global_suggestions = 5
        target_suggestions = None

        if use_global_mode:
            try:
                raw = input("➡️ How many global images per base? (ENTER = 5): ").strip()
                global_suggestions = max(1, int(raw) if raw else 5)
            except ValueError:
                global_suggestions = 5
            print(f"\n🎯 Each base will receive {global_suggestions} suggestions inspired by the full text.")
        else:
            try:
                g = input("➡️ How many speeches per scene? (ENTER = 1): ").strip()
                group_size = max(1, int(g) if g else 1)
            except ValueError:
                group_size = 1

            print("\n🎯 Scenes to process (per file):")
            for base in selected:
                count = sentence_counts.get(base)
                if not count:
                    print(f" - {base}: will not be processed (no sentences)")
                    continue
                total_scenes = (count + group_size - 1) // group_size
                print(f" - {base}: {total_scenes} scenes (group={group_size})")

        profiles = list_profiles()
        chosen_profiles = choose_profiles(profiles)

        for base in selected:
            if use_global_mode:
                process_base_full_script(base, global_suggestions, chosen_profiles)
            else:
                # Calls corrected Per-Scene mode
                process_base(base, group_size, chosen_profiles, target_suggestions)

    finally:
        ring_bell("✅ Finished processing selected bases.")

if __name__ == "__main__":
    main()
