import os
import requests
from dotenv import load_dotenv
from pathlib import Path
from support_scripts.manifesto import load_manifest, update_stage
from support_scripts.paths import AUDIO_OUTPUT_DIR

# --- 1. Configuração ---
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

API_KEY = os.getenv('GENPROAI_API_KEY')
BASE_URL = "https://genaipro.vn/api/v1" 
URL_LIST = f"{BASE_URL}/labs/tasks"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def download_file(url, output_path):
    """Downloads the file from the URL and saves it to the specified path."""
    try:
        print(f"⬇️ Downloading: {url}")
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(output_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"✅ Saved to: {output_path}")
        return True
    except Exception as e:
        print(f"❌ Download error: {e}")
        return False

def main():
    if not API_KEY:
        print("❌ Error: GENPROAI_API_KEY not found in .env file")
        return

    # 1. Load Manifest and Filter Pending Downloads
    mf = load_manifest()
    pending_downloads = {
        base: info.get("audio_id") 
        for base, info in mf.items() 
        if info.get("audio") == "done" 
        and info.get("audio_downloaded") != "done" 
        and info.get("audio_id")
    }

    if not pending_downloads:
        print("📭 No audio pending download in manifest.")
        return

    print(f"🔍 Checking status for {len(pending_downloads)} pending tasks...")

    # --- USER SELECTION ---
    pending_list = list(pending_downloads.items()) # [(base, audio_id), ...]

    print(f"\n🎧 Audios available for download:")
    for i, (base, _) in enumerate(pending_list, 1):
        print(f"{i}. {base}")
    print("0. All")

    selection = input("\n➡️ Select (e.g. 1 3 or '0' for all): ").strip()
    
    selected_items = []
    if selection == '0' or selection.lower() == 'all':
        selected_items = pending_list
    else:
        try:
            # Supports space or comma separation
            indices = [int(x) - 1 for x in selection.replace(',', ' ').split()]
            for idx in indices:
                if 0 <= idx < len(pending_list):
                    selected_items.append(pending_list[idx])
        except ValueError:
            print("❌ Invalid input.")
            return

    if not selected_items:
        print("⚠️ No items selected.")
        return

    print(f"\n🚀 Processing {len(selected_items)} items...")

    # 2. Check Status and Download
    downloaded_count = 0

    for base_name, audio_id in selected_items:
        task_url = f"{BASE_URL}/labs/task/{audio_id}"
        print(f"🔍 Checking task {audio_id} for '{base_name}'...")
        
        try:
            response = requests.get(task_url, headers=headers)
            if response.status_code != 200:
                print(f"⚠️ Error querying task {audio_id}: {response.status_code}")
                continue
            
            task = response.json()
            
            # Identify status and result
            status = str(task.get("status") or task.get("state") or "").upper()
            result_url = task.get("result") or task.get("output") or task.get("url")

            print(f"   Status: {status}")

            if status in ["COMPLETED", "SUCCESS", "DONE"] and result_url:
                # Prepare output path
                AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
                output_path = AUDIO_OUTPUT_DIR / f"{base_name}.mp3"
                
                if download_file(result_url, output_path):
                    update_stage(base_name, "audio_downloaded", "done", extra={"audio_file": str(output_path)})
                    downloaded_count += 1
            elif status in ["FAILED", "ERROR"]:
                 print(f"❌ Task failed at API.")
        
        except Exception as e:
            print(f"❌ Error processing task {audio_id}: {e}")

    if downloaded_count == 0:
        print("ℹ️ No download performed (tasks might be processing).")
    else:
        print(f"🎉 {downloaded_count} audio(s) downloaded successfully.")

if __name__ == "__main__":
    main()