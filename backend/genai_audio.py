#!/usr/bin/env python3
"""
GenAI Pro Audio Generator - Standalone Script
==============================================
This script generates audio from text using the GenAI Pro API.

Configuration:
1. Set your API key in the GENAI_API_KEY variable below
2. Set your input text in the TEXT_TO_CONVERT variable
3. Run: python genai_audio.py

The script will:
- Display your account balance
- Submit the text for audio generation
- Return a task ID that you can use with genai_download.py
"""

import os
import re
import requests
from pathlib import Path

# =============================================================================
# CONFIGURATION - Edit these values
# =============================================================================

# Your GenAI Pro API Key (get it from https://genaipro.vn)
GENAI_API_KEY = "your_api_key_here"

# Text to convert to audio (can be multiple lines)
TEXT_TO_CONVERT = """
Hello, this is a test of the GenAI Pro audio generation API.
This text will be converted to speech.
You can add multiple sentences here.
"""

# Voice settings (optional)
VOICE_ID = "xxxxxxxxxxxxxxx"  # Change to your preferred voice
SPEED = 1.0  # Speech speed (0.5 to 2.0)
PITCH = 1.0  # Voice pitch (0.5 to 2.0)
MODEL_ID = "eleven_multilingual_v2"

# API Configuration (usually don't need to change)
API_BASE_URL = "https://genaipro.vn/api/v1"

# =============================================================================
# Script Logic - No need to edit below this line
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
    url = f"{API_BASE_URL}/labs/tts"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "text": text,
        "voiceId": voice_id,
        "speed": speed,
        "pitch": pitch,
        "modelId": model_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            task_id = data.get("id")
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


def main():
    print("=" * 70)
    print("GenAI Pro Audio Generator")
    print("=" * 70)
    
    # Validate API key
    if GENAI_API_KEY == "your_api_key_here" or not GENAI_API_KEY:
        print("\n❌ ERROR: Please set your GENAI_API_KEY in the script!")
        print("   Get your API key from: https://genaipro.vn")
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
    
    # Clean and prepare text
    cleaned_text = clean_text(TEXT_TO_CONVERT)
    
    if not cleaned_text:
        print("\n❌ ERROR: No text to convert!")
        return
    
    print(f"\n📝 Text to convert ({len(cleaned_text)} characters):")
    preview = cleaned_text[:100] + "..." if len(cleaned_text) > 100 else cleaned_text
    print(f"   {preview}")
    
    # Generate audio
    print(f"\n🎤 Submitting to GenAI Pro API...")
    print(f"   Voice: {VOICE_ID}")
    print(f"   Speed: {SPEED}x")
    print(f"   Pitch: {PITCH}x")
    
    result = generate_audio(GENAI_API_KEY, cleaned_text, VOICE_ID, SPEED, PITCH)
    
    if result["success"]:
        print(f"\n✅ Audio generation started successfully!")
        print(f"   Task ID: {result['task_id']}")
        print(f"   Status: {result['status']}")
        print(f"\n💡 Next steps:")
        print(f"   1. Save this Task ID: {result['task_id']}")
        print(f"   2. Use genai_download.py to download the audio when ready")
        print(f"   3. Or check status at: {API_BASE_URL}/labs/task/{result['task_id']}")
    else:
        print(f"\n❌ Audio generation failed!")
        print(f"   Error: {result['error']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
