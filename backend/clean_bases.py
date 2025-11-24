import json
import shutil
import os
from pathlib import Path
from support_scripts.paths import (
    MANIFEST_PATH,
    VIDEO_OUTPUT_DIR,
    IMG_OUTPUT_DIR,
    RENDER_OUTPUT_DIR,
    SCRIPTS_RENDER_DIR,
    SRT_OUTPUT_DIR,
    TIMELINES_DIR,
    IMG_SUGGESTIONS_DIR,
    TXT_INBOX_DIR,
    TXT_PROCESSED_DIR,
    AUDIO_OUTPUT_DIR,
    OUTPUT_ROOT,
)

# ========================
# CONFIG
# ========================
ROOT = Path(__file__).resolve().parent
VIDEOS_DIR = VIDEO_OUTPUT_DIR
IMGS_DIR = IMG_OUTPUT_DIR
RENDER_DIR = RENDER_OUTPUT_DIR
SRT_DIR = SRT_OUTPUT_DIR
TIMELINE_DIR = TIMELINES_DIR
TXT_INBOX = TXT_INBOX_DIR
TXT_PROCESSED = TXT_PROCESSED_DIR
AUDIO_DIR = AUDIO_OUTPUT_DIR

# ========================
# HELPERS
# ========================
def delete_path(p: Path):
    """Deletes file or entire folder."""
    try:
        if p.is_file():
            p.unlink()
            print(f"🗑️  File deleted: {p}")
        elif p.is_dir():
            shutil.rmtree(p)
            print(f"🧹 Folder deleted: {p}")
    except Exception as e:
        print(f"⚠️ Failed to delete {p}: {e}")

def clean_by_pattern(target_name):
    """
    Scans OUTPUT_ROOT and deletes files/folders whose name contains 'target_name'.
    Preserves TXT_PROCESSED_DIR and its contents.
    """
    print(f"🕵️  Scanning OUTPUT to remove items containing: '{target_name}'")
    
    target = str(target_name)
    
    for root, dirs, files in os.walk(OUTPUT_ROOT, topdown=True):
        root_path = Path(root)
        
        # If it's the protected folder or inside it, skip
        if root_path == TXT_PROCESSED_DIR or TXT_PROCESSED_DIR in root_path.parents:
            dirs[:] = [] # Do not descend further
            continue

        # Check directories to delete
        # Iterate over a copy to modify original 'dirs' list and avoid recursion in deleted folders
        for dir_name in dirs[:]:
            if target in dir_name:
                full_dir_path = root_path / dir_name
                
                # Extra protection
                if full_dir_path == TXT_PROCESSED_DIR:
                    dirs.remove(dir_name)
                    continue
                
                delete_path(full_dir_path)
                dirs.remove(dir_name) # Ensures os.walk doesn't try to enter it
        
        # Verifica arquivos
        for file_name in files:
            if target in file_name:
                file_path = root_path / file_name
                delete_path(file_path)

def load_manifest():
    """Loads the manifest and returns the dictionary."""
    if not MANIFEST_PATH.exists():
        print("⚠️ Manifest not found, creating new empty one.")
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text("{}", encoding="utf-8")
        return {}
    try:
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"⚠️ Error reading manifest: {e}")
        return {}

def save_manifest(data):
    """Saves the updated manifest."""
    try:
        MANIFEST_PATH.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"🧾 Manifest updated: {MANIFEST_PATH}")
    except Exception as e:
        print(f"⚠️ Failed to save manifest: {e}")

def select_videos(manifest_data):
    """Lists all manifest items and allows choosing which to clean."""
    all_items = list(manifest_data.keys())
    if not all_items:
        print("⚠️ No items found in manifest.")
        return []

    print("\n📜 Items available for cleaning:")
    for i, item in enumerate(all_items, start=1):
        print(f"[{i}] {item}")
    print("[0] ALL (WARNING: Deletes everything!)")

    selected = input("\nEnter numbers of items to clean (e.g. 1,3,5) or 0 for ALL: ").strip()
    if not selected:
        print("🚫 No items selected. Aborting cleaning.")
        return []

    try:
        indices = [int(x.strip()) for x in selected.split(",")]
        
        if 0 in indices:
            print("\n⚠️  WARNING: You selected DELETE ALL!")
            confirm = input("Are you absolutely sure? Type 'yes' to confirm: ").strip().lower()
            if confirm == 'yes':
                print("\n✅ All items selected for cleaning.")
                return all_items
            else:
                print("🚫 Operation cancelled.")
                return []

        chosen = [all_items[i - 1] for i in indices if 1 <= i <= len(all_items)]
        print(f"\n✅ Selected for cleaning: {chosen}")
        return chosen
    except Exception:
        print("⚠️ Invalid input. Aborting.")
        return []

def clean_video_files(video_name):
    """Deletes all files related to the video and moves processed TXT."""
    # Folders first
    dir_candidates = [
        IMGS_DIR / video_name,
        (IMG_SUGGESTIONS_DIR / video_name),
        VIDEOS_DIR / video_name,
        RENDER_DIR / video_name,
        SCRIPTS_RENDER_DIR / video_name,
    ]
    for path in dir_candidates:
        if path.exists():
            delete_path(path)

    # Specific files
    file_candidates = [
        VIDEOS_DIR / f"{video_name}.mp4",
        RENDER_DIR / f"{video_name}.mp4",
        SCRIPTS_RENDER_DIR / f"{video_name}.mp4",
        SRT_DIR / f"{video_name}.srt",
        TIMELINE_DIR / f"{video_name}_timeline.json",
        AUDIO_DIR / f"{video_name}.mp3",
    ]
    seen = set()
    for path in file_candidates:
        if path.exists():
            key = str(path.resolve())
            if key in seen:
                continue
            delete_path(path)
            seen.add(key)

    # Deep scan by name pattern
    clean_by_pattern(video_name)

    # move_txt_to_processed(video_name)

def purge_output_except_txt_processed():
    """Removes everything in output/ except output/txt_processed."""
    if not OUTPUT_ROOT.exists():
        return

    preserved = TXT_PROCESSED_DIR.resolve()

    print("\n🧨 Cleaning output/ content (except txt_processed)...")
    for child in OUTPUT_ROOT.iterdir():
        resolved = child.resolve()
        if resolved == preserved:
            continue
        delete_path(child)

# ========================
# MAIN
# ========================
def main():
    print("💣 Starting manifest verification...\n")
    manifest_data = load_manifest()
    selected_videos = select_videos(manifest_data)

    if not selected_videos:
        print("\n🚫 No action performed.")
        return

    print("\n🔥 Cleaning selected data...\n")

    # Checks if all were selected to decide whether to run full purge
    is_full_clean = (len(selected_videos) == len(manifest_data)) and (len(manifest_data) > 0)

    for video_name in selected_videos:
        clean_video_files(video_name)
        if video_name in manifest_data:
            del manifest_data[video_name]

    save_manifest(manifest_data)
    
    if is_full_clean:
        purge_output_except_txt_processed()
        
    print("\n✅ Cleanup completed successfully.")

if __name__ == "__main__":
    main()


def move_txt_to_processed(base_name: str):
    TXT_PROCESSED.mkdir(parents=True, exist_ok=True)
    src = TXT_INBOX / f"{base_name}.txt"
    if not src.exists():
        return
    dest = TXT_PROCESSED / src.name
    try:
        if dest.exists():
            dest.unlink()
        src.replace(dest)
        print(f"📁 TXT moved to {dest}")
    except Exception as exc:
        print(f"⚠️ Failed to move {src}: {exc}")
