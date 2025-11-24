import os
import re
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
from support_scripts.manifesto import load_manifest, update_stage
from support_scripts.paths import TXT_INBOX_DIR

# --- 1. Configuração e Carregamento de Variáveis de Ambiente ---
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

API_KEY = os.getenv('GENPROAI_API_KEY')
BASE_URL = "https://genaipro.vn/api/v1" 

# Configurações do Áudio
VOICE_ID = "f5HLTX707KIM4SzJYzSz"
MODEL_ID = "eleven_multilingual_v2"
SPEED = 0.9

# Headers para autenticação
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

def clean_text(text):
    """Remove all XML-like tags (<...>) from the text."""
    return re.sub(r'<[^>]+>', '', text).strip()

def create_task(url, headers, payload):
    """Sends POST request to create audio task and returns task_id."""
    print("--- 🛠️ Starting Task Creation (POST /labs/task) ---")
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("task_id") 
            
            if task_id:
                print(f"✅ Task created successfully! ID: {task_id}")
                return task_id
            else:
                print("❌ Error: 'task_id' not found in response.")
                return None
        else:
            print(f"❌ Failed to create task. Status: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"❌ Connection/Execution Error: {e}")
        return None

def check_balance(base_url, headers):
    """Query and display user balance."""
    try:
        response = requests.get(f"{base_url}/me", headers=headers)
        if response.status_code == 200:
            data = response.json()
            balance = data.get("balance", "N/A")
            credits_list = data.get("credits", [])
            
            # If balance is N/A or 0, try summing credits
            total_credits = sum(float(c.get("amount", 0)) for c in credits_list)
            
            balance_str = f"{float(balance):,.2f}" if isinstance(balance, (int, float)) and balance != "N/A" else str(balance)
            credits_str = f"{total_credits:,.2f}"

            print(f"\n💰 Available Balance: {balance_str} | Total Credits: {credits_str}")
        else:
            print(f"⚠️ Error querying balance: {response.status_code}")
    except Exception as e:
        print(f"⚠️ Connection error querying balance: {e}")

def main():
    if not API_KEY:
        print("❌ Error: GENPROAI_API_KEY not found in .env file")
        return

    # 0. Check Balance
    check_balance(BASE_URL, headers)

    # 1. Load Manifest and Filter Pending
    mf = load_manifest()
    pending_bases = [b for b, info in mf.items() if info.get("audio") == "pending" and info.get("txt") == "done"]

    if not pending_bases:
        print("📭 No bases with 'audio: pending' found.")
        return

    print("\n🎙️ Pending bases for audio generation:")
    for i, base in enumerate(pending_bases, 1):
        print(f"[{i}] {base}")
    print("[0] Process ALL")

    # 2. User Selection
    selection = input("\nEnter base number (e.g. 1) or '0' for all: ").strip()
    
    bases_to_process = []

    if selection == "0":
        print("🚀 Selected: Process ALL pending bases.")
        bases_to_process = pending_bases
    else:
        try:
            idx = int(selection) - 1
            if 0 <= idx < len(pending_bases):
                bases_to_process = [pending_bases[idx]]
            else:
                print("❌ Invalid selection.")
                return
        except ValueError:
            print("❌ Invalid input.")
            return

    # 3. Process Selected Items
    for base_name in bases_to_process:
        print(f"\n🚀 Processing: {base_name}")

        # Read and Clean Text
        txt_path = TXT_INBOX_DIR / f"{base_name}.txt"
        if not txt_path.exists():
            print(f"❌ Text file not found: {txt_path}")
            continue

        raw_text = txt_path.read_text(encoding="utf-8")
        cleaned_text = clean_text(raw_text)

        if not cleaned_text:
            print("❌ Text is empty after cleaning.")
            continue

        print(f"📝 Cleaned text (first 100 chars): {cleaned_text[:100]}...")

        # Send to API
        payload = {
            "input": cleaned_text,
            "voice_id": VOICE_ID,
            "model_id": MODEL_ID,
            "speed": SPEED
        }
        
        post_url = f"{BASE_URL}/labs/task"
        task_id = create_task(post_url, headers, payload)

        # Update Manifest
        if task_id:
            update_stage(base_name, "audio", "done", extra={"audio_id": task_id, "audio_downloaded": "pending"})
            print(f"✅ Manifest updated for {base_name}: audio=done, audio_id={task_id}")
        else:
            print("⚠️ Audio generation failed. Manifest not updated.")

if __name__ == "__main__":
    main()