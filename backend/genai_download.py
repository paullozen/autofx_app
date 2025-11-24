#!/usr/bin/env python3
"""
GenAI Pro Audio Downloader - Standalone Script
===============================================
This script downloads generated audio files from the GenAI Pro API.

Configuration:
1. Set your API key in the GENAI_API_KEY variable below
2. Set the task ID(s) in the TASK_IDS list
3. Set the output directory in OUTPUT_DIR
4. Run: python genai_download.py

The script will:
- Check the status of each task
- Download completed audio files
- Save them to the specified output directory
"""

import os
import requests
from pathlib import Path
from datetime import datetime

# =============================================================================
# CONFIGURATION - Edit these values
# =============================================================================

# Your GenAI Pro API Key (get it from https://genaipro.vn)
GENAI_API_KEY = "your_api_key_here"

# Task IDs to download (get these from genai_audio.py output)
# You can add multiple task IDs here
TASK_IDS = [
    # "task_id_1",
    # "task_id_2",
    # "task_id_3",
]

# Output directory for downloaded audio files
OUTPUT_DIR = "/audio_output"

# API Configuration (usually don't need to change)
API_BASE_URL = "https://genaipro.vn/api/v1"

# =============================================================================
# Script Logic - No need to edit below this line
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


def main():
    print("=" * 70)
    print("GenAI Pro Audio Downloader")
    print("=" * 70)
    
    # Validate API key
    if GENAI_API_KEY == "your_api_key_here" or not GENAI_API_KEY:
        print("\n❌ ERROR: Please set your GENAI_API_KEY in the script!")
        print("   Get your API key from: https://genaipro.vn")
        return
    
    # Validate task IDs
    if not TASK_IDS:
        print("\n❌ ERROR: No task IDs specified!")
        print("   Add task IDs to the TASK_IDS list in the script.")
        print("   Example: TASK_IDS = ['task_abc123', 'task_def456']")
        return
    
    # Create output directory
    output_dir = Path(OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📁 Output directory: {output_dir.absolute()}")
    print(f"📋 Tasks to check: {len(TASK_IDS)}")
    
    # Process each task
    results = {
        "completed": [],
        "pending": [],
        "failed": [],
        "downloaded": 0,
        "errors": 0
    }
    
    for idx, task_id in enumerate(TASK_IDS, 1):
        print(f"\n{'─' * 70}")
        print(f"[{idx}/{len(TASK_IDS)}] Task: {task_id}")
        
        # Check task status
        print("   Checking status...")
        status_result = get_task_status(GENAI_API_KEY, task_id)
        
        if not status_result["success"]:
            print(f"   ❌ Error: {status_result['error']}")
            results["errors"] += 1
            results["failed"].append(task_id)
            continue
        
        status = status_result["status"]
        print(f"   Status: {status}")
        
        if status in ["completed", "done", "success"]:
            result_url = status_result.get("result_url")
            
            if not result_url:
                print("   ⚠️  No download URL available")
                results["failed"].append(task_id)
                continue
            
            # Generate output filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audio_{task_id[:8]}_{timestamp}.mp3"
            output_path = output_dir / filename
            
            # Download audio
            print(f"   📥 Downloading...")
            download_result = download_audio(result_url, output_path)
            
            if download_result["success"]:
                file_size = format_size(download_result["size"])
                print(f"   ✅ Downloaded: {filename} ({file_size})")
                results["downloaded"] += 1
                results["completed"].append(task_id)
            else:
                print(f"   ❌ Download failed: {download_result['error']}")
                results["errors"] += 1
                results["failed"].append(task_id)
        
        elif status in ["pending", "processing", "in_progress"]:
            print(f"   ⏳ Task is still processing")
            results["pending"].append(task_id)
        
        else:
            print(f"   ❌ Task failed or has unknown status: {status}")
            results["failed"].append(task_id)
    
    # Summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    print(f"✅ Downloaded: {results['downloaded']}")
    print(f"⏳ Pending: {len(results['pending'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    print(f"⚠️  Errors: {results['errors']}")
    
    if results["pending"]:
        print(f"\n⏳ Pending tasks ({len(results['pending'])}):")
        for task_id in results["pending"]:
            print(f"   - {task_id}")
        print("   Run this script again later to download them.")
    
    if results["failed"]:
        print(f"\n❌ Failed tasks ({len(results['failed'])}):")
        for task_id in results["failed"]:
            print(f"   - {task_id}")
    
    if results["downloaded"] > 0:
        print(f"\n📁 Audio files saved to: {output_dir.absolute()}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
