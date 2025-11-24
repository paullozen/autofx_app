# create_chrome_profile.py
import asyncio
from pathlib import Path
from datetime import datetime
from playwright.async_api import async_playwright

# ==========================
# CONFIG
# ==========================
ROOT           = Path(__file__).resolve().parent
PROFILE_FOLDER = ROOT / "chrome_profiles"
START_URLS = [
    # Open ImageFX directly (will ask for Google login)
    "https://labs.google/fx/tools/image-fx",
    # Useful fallbacks if you prefer to authenticate here
    "https://accounts.google.com/",
    "https://www.google.com/",
]


# ==========================
# HELPERS
# ==========================
def list_profiles() -> list[str]:
    if not PROFILE_FOLDER.exists():
        return []
    return sorted([p.name for p in PROFILE_FOLDER.iterdir() if p.is_dir()])

def sanitize_name(name: str) -> str:
    name = name.strip().replace("\\", "_").replace("/", "_").replace(":", "_")
    name = name.replace("*", "_").replace("?", "_").replace('"', "_")
    name = name.replace("<", "_").replace(">", "_").replace("|", "_")
    return name or datetime.now().strftime("profile_%Y%m%d_%H%M%S")

def ensure_profile_dir(profile_name: str) -> Path:
    """
    Creates chrome_profiles/<profile_name>/Default folder and removes possible locks.
    Returns the user_data_dir path (the profile folder).
    """
    PROFILE_FOLDER.mkdir(parents=True, exist_ok=True)
    user_data_dir = PROFILE_FOLDER / profile_name
    default_dir = user_data_dir / "Default"
    default_dir.mkdir(parents=True, exist_ok=True)

    # Remove locks (helps on Windows)
    for lock_name in ("SingletonLock", "SingletonCookie", "SingletonSocket"):
        p = default_dir / lock_name
        try:
            if p.exists():
                p.unlink()
        except Exception:
            pass

    return user_data_dir


# ==========================
# CORE
# ==========================
async def create_profile_interactive(profile_name: str = None) -> str:
    """
    Creates a new persistent Chrome profile and opens a window
    for you to log in. Keeps the window open until you press ENTER.
    Returns the name of the created profile.
    """
    existing = list_profiles()
    if existing:
        print("Existing profiles:")
        for i, name in enumerate(existing, 1):
            print(f"  {i}. {name}")
        print()

    # If no name provided, ask for input
    if not profile_name:
        raw = input("🆕 New profile name (ENTER suggests automatic): ").strip()
        profile_name = sanitize_name(raw) if raw else datetime.now().strftime("profile_%Y%m%d_%H%M%S")
    else:
        profile_name = sanitize_name(profile_name)
        print(f"🆕 Creating profile: {profile_name}")

    if profile_name in existing:
        print(f"⚠️ A profile named '{profile_name}' already exists. I will append a date/time suffix.")
        profile_name = f"{profile_name}_{datetime.now().strftime('%H%M%S')}"

    user_data_dir = ensure_profile_dir(profile_name)
    print(f"✅ Profile folder: {user_data_dir}")

    async with async_playwright() as pw:
        # Open Chrome with persistent profile
        context = await pw.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            channel="chrome",
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-first-run", "--no-default-browser-check",
                "--disable-infobars",
            ],
        )

        # Simple anti-detections
        await context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            if (!window.chrome) window.chrome = { runtime: {} };
        """)

        page = await context.new_page()
        # Try opening ImageFX first (will ask for Google login)
        for url in START_URLS:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=45000)
                break
            except Exception:
                pass

        # Keeps Chrome open and waits for closure
        try:
            # Waits until context is closed (when user closes browser)
            await context.wait_for_event('close', timeout=0)
        except Exception:
            # If timeout or error, try to close context
            try:
                await context.close()
            except Exception:
                # Context already closed, ignore
                pass

    print(f"🎉 Profile '{profile_name}' created/ready for use.")
    return profile_name


def main():
    import sys
    # Accepts profile name as argument
    profile_name = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(create_profile_interactive(profile_name))


if __name__ == "__main__":
    main()
