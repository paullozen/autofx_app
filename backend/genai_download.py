#!/usr/bin/env python3
"""
GenAI Pro Audio Downloader - Integrated Script
===============================================
This script downloads generated audio files from the GenAI Pro API.
It reads configuration from .env and processes tasks from manifesto.json.
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
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
OUTPUT_DIR = BASE_DIR / "output" / "audio"

# API Configuration
GENAI_API_KEY = os.getenv("GENAIPRO_API_KEY")
API_BASE_URL = "https://genaipro.vn/api/v1"

# =============================================================================
# Script Logic
# =============================================================================

def get_task_status(api_key: str, task_id: str) -> dict:
    """Get the status of a specific task."""
    url = f"{API_BASE_URL}/labs/task/{task_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "status": data.get("status", "unknown").lower(),
                "result_url": data.get("result"),
                "data": data
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

def download_audio(url: str, output_path: Path) -> dict:
    """Download audio file from URL."""
    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            file_size = output_path.stat().st_size
            return {
                "success": True,
                "path": str(output_path),
                "size": file_size
            }
        else:
            return {
                "success": False,
                "error": f"Download failed with status {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

def format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"

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
    print("GenAI Pro Audio Downloader - Batch Processor")
    print("=" * 70)
    
    # Validate API key
    if not GENAI_API_KEY:
        print(f"\n❌ ERROR: GENAIPRO_API_KEY not found in .env file!")
        print(f"   Expected .env location: {ENV_PATH}")
        print("   Please ensure the file exists and contains GENAIPRO_API_KEY=your_key")
        return
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Output directory: {OUTPUT_DIR.absolute()}")
    
    # Load Manifest
    manifest = load_manifest()
    if not manifest:
        return

    # Load Manifest
    manifest = load_manifest()
    if not manifest:
        return

    print(f"\n📋 Scanning manifesto.json for pending downloads...")
    
    pending_items = []
    for project_name, data in manifest.items():
        # Check status
        if data.get("audio_downloaded") == "done":
            continue
            
        # Check if audio_id exists
        if not data.get("audio_id"):
            continue
            
        pending_items.append(project_name)

    if not pending_items:
        print("✅ No pending downloads found in manifesto.json.")
        return

    print(f"\n📜 Pending Downloads ({len(pending_items)}):")
    for i, proj in enumerate(pending_items, 1):
        task_id = manifest[proj].get("audio_id")
        print(f"   {i}. {proj}")
        print(f"      Task ID: {task_id}")

    # Interactive selection
    try:
        selection = input("\nSelect a project number (or ENTER for ALL, 'q' to quit): ").strip()
        if selection.lower() == 'q':
            return
        
        projects_to_process = []
        if not selection:
            print("🚀 Selected: Process ALL pending downloads.")
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
        print(f"\n🎬 Project: {project_name}")
        data = manifest[project_name]
        
        task_id = data.get("audio_id")
        print(f"   Task ID: {task_id}")
        
        # Check task status
        print("   Checking status...")
        status_result = get_task_status(GENAI_API_KEY, task_id)
        
        if not status_result["success"]:
            print(f"   ❌ Error: {status_result['error']}")
            continue
        
        status = status_result["status"]
        print(f"   Status: {status}")
        
        if status in ["completed", "done", "success"]:
            result_url = status_result.get("result_url")
            
            if not result_url:
                print("   ⚠️  No download URL available")
                continue
            
            # Generate output filename
            safe_name = "".join([c for c in project_name if c.isalpha() or c.isdigit() or c in (' ', '-', '_')]).rstrip()
            filename = f"{safe_name}.mp3"
            output_path = OUTPUT_DIR / filename
            
            # Download audio
            print(f"   📥 Downloading...")
            download_result = download_audio(result_url, output_path)
            
            if download_result["success"]:
                file_size = format_size(download_result["size"])
                print(f"   ✅ Downloaded: {filename} ({file_size})")
                
                # Update manifest
                manifest[project_name]["audio_downloaded"] = "done"
                manifest[project_name]["audio"] = "done"
                
                rel_path = output_path.relative_to(BASE_DIR)
                manifest[project_name]["audio_file"] = str(rel_path)
                
                updates_made = True
            else:
                print(f"   ❌ Download failed: {download_result['error']}")
        
        elif status in ["pending", "processing", "in_progress"]:
            print(f"   ⏳ Task is still processing. Please try again later.")
        
        else:
            print(f"   ❌ Task failed or has unknown status: {status}")
    
    if updates_made:
        save_manifest(manifest)
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    main()
