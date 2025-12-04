#!/usr/bin/env python3
"""
GenAI Pro Audio Generator - Integrated Script
==============================================
This script generates audio from text using the GenAI Pro API.
It reads configuration from .env and processes tasks from manifesto.json.
"""

import os
import re
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
# Explicitly look for .env in the same directory as this script
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

# =============================================================================
# CONFIGURATION
# =============================================================================

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
MANIFEST_PATH = BASE_DIR / "manifesto.json"
TXT_INBOX_DIR = BASE_DIR / "txt_inbox"

# API Configuration
GENAI_API_KEY = os.getenv("GENAIPRO_API_KEY")
VOICE_ID = os.getenv("GENAIPRO_VOICE")
API_BASE_URL = "https://genaipro.vn/api/v1"

# Voice settings
SPEED = 1.0
PITCH = 1.0
MODEL_ID = "eleven_multilingual_v2"

# =============================================================================
# Script Logic
# =============================================================================

def clean_text(text: str) -> str:
    """Remove XML-like tags and clean the text."""
    cleaned = re.sub(r'<[^>]+>', '', text)
    cleaned = re.sub(r'\s+', ' ', cleaned)
    return cleaned.strip()

def check_balance(api_key: str) -> dict:
    """Check account balance and credits."""
    url = f"{API_BASE_URL}/me"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            balance = float(data.get("balance", 0))
            total_credits = float(data.get("totalCredits", 0))
            return {
                "success": True,
                "balance": balance,
                "total_credits": total_credits
            }
        else:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def generate_audio(api_key: str, text: str, voice_id: str, speed: float, pitch: float) -> dict:
    """Submit text for audio generation."""
    # Use the task creation endpoint
    url = f"{API_BASE_URL}/labs/task"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload structure matching audio_generator.py
    payload = {
        "input": text,
        "voice_id": voice_id,
        "model_id": MODEL_ID,
        "speed": speed
        # Pitch is not used in audio_generator.py, omitting to be safe
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            # audio_generator.py looks for 'task_id'
            task_id = data.get("task_id") or data.get("id")
            return {
                "success": True,
                "task_id": task_id,
                "status": data.get("status", "pending")
            }
        else:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}: {response.text}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def load_manifest():
    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest file not found at {MANIFEST_PATH}")
        return {}
    try:
        with open(MANIFEST_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading manifest: {e}")
        return {}

def save_manifest(data):
    try:
        with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("💾 Manifest updated.")
    except Exception as e:
        print(f"❌ Error saving manifest: {e}")

def main():
    print("=" * 70)
    print("GenAI Pro Audio Generator - Batch Processor")
    print("=" * 70)
    
    # Validate API key
    if not GENAI_API_KEY:
        print(f"\n❌ ERROR: GENAIPRO_API_KEY not found in .env file!")
        print(f"   Expected .env location: {ENV_PATH}")
        print("   Please ensure the file exists and contains GENAIPRO_API_KEY=your_key")
        return

    if not VOICE_ID:
        print(f"\n❌ ERROR: GENAIPRO_VOICE not found in .env file!")
        print(f"   Expected .env location: {ENV_PATH}")
        print("   Please ensure the file exists and contains GENAIPRO_VOICE=your_voice_id")
        return
    
    # Check balance
    print("\n📊 Checking account balance...")
    balance_result = check_balance(GENAI_API_KEY)
    
    if balance_result["success"]:
        balance = balance_result["balance"]
        total_credits = balance_result["total_credits"]
        print(f"   Balance: ${balance:,.2f}")
        print(f"   Total Credits: {total_credits:,.2f}")
    else:
        print(f"   ⚠️  Could not fetch balance: {balance_result['error']}")
    
    # Load Manifest
    manifest = load_manifest()
    if not manifest:
        return

    # Load Manifest
    manifest = load_manifest()
    if not manifest:
        return

    print(f"\n📋 Scanning manifesto.json for pending audio tasks...")
    
    pending_items = []
    for project_name, data in manifest.items():
        # Check status
        if data.get("audio") == "done":
            continue
            
        # Check if txt file is defined
        txt_file = data.get("txt_file")
        if not txt_file:
            continue
            
        # We verify existence later during processing to list it even if missing (so user knows)
        pending_items.append(project_name)

    if not pending_items:
        print("✅ No pending audio tasks found in manifesto.json.")
        return

    print(f"\n📜 Pending Projects ({len(pending_items)}):")
    for i, proj in enumerate(pending_items, 1):
        txt_file = manifest[proj].get("txt_file")
        print(f"   {i}. {proj}")
        print(f"      File: {txt_file}")

    # Interactive selection
    try:
        selection = input("\nSelect a project number to process (or ENTER for ALL, 'q' to quit): ").strip()
        if selection.lower() == 'q':
            return
        
        projects_to_process = []
        if not selection:
            print("🚀 Selected: Process ALL pending projects.")
            projects_to_process = pending_items
        else:
            idx = int(selection) - 1
            if not (0 <= idx < len(pending_items)):
                print("❌ Invalid selection.")
                return
            projects_to_process = [pending_items[idx]]
            print(f"\n✅ Selected: {projects_to_process[0]}")
        
    except ValueError:
        print("❌ Invalid input. Please enter a number or press ENTER.")
        return

    # Process selected projects
    updates_made = False
    
    for project_name in projects_to_process:
        print(f"\n🎬 Processing: {project_name}")
        data = manifest[project_name]
        
        txt_rel_path = data.get("txt_file")
        if not txt_rel_path:
            print("   ❌ No txt_file entry in manifest.")
            continue
            
        txt_path = BASE_DIR / txt_rel_path
        if not txt_path.exists():
            print(f"   ❌ Text file not found: {txt_path}")
            continue
        
        # Read text
        try:
            text_content = txt_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"   ❌ Error reading text file: {e}")
            continue

        cleaned_text = clean_text(text_content)
        if not cleaned_text:
            print("   ⚠️  Text file is empty or invalid.")
            continue
            
        print(f"   📝 Text length: {len(cleaned_text)} chars")
        
        # Generate Audio
        print(f"   🎤 Submitting to GenAI Pro API...")
        result = generate_audio(GENAI_API_KEY, cleaned_text, VOICE_ID, SPEED, PITCH)
        
        if result["success"]:
            task_id = result["task_id"]
            print(f"   ✅ Started! Task ID: {task_id}")
            
            # Update manifest
            manifest[project_name]["audio_id"] = task_id
            manifest[project_name]["audio"] = "done"
            manifest[project_name]["audio_downloaded"] = "pending"
            updates_made = True
        else:
            print(f"   ❌ Failed: {result['error']}")

    if updates_made:
        save_manifest(manifest)
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
