import os
import sys
from pathlib import Path

# Add project root to path to allow imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from support_scripts.paths import IMG_SUGGESTIONS_DIR

# ==========================================
# CONFIGURATION
# ==========================================

# 1. Automatic Replacements: { "search_term": "replacement_term" }
# These will be replaced automatically without asking.
AUTO_REPLACEMENTS = {
    "Youtuber": "Creator",
    "youtuber": "creator",
    "person": "creator",
    'Person': 'Creator',
}

# 2. Manual Replacements: [ "search_term1", "search_term2" ]
# The script will find these terms and ASK you what to replace them with.
MANUAL_TERMS_TO_FIND = [
    "Youtuber",
    "youtuber",
    "person",
    "Person"
]

# ==========================================
# SCRIPT
# ==========================================

def main():
    print("🚀 Starting Name Changes Script...")
    print(f"📂 Scanning directory: {IMG_SUGGESTIONS_DIR}")

    if not IMG_SUGGESTIONS_DIR.exists():
        print("❌ Suggestions directory not found.")
        return

    # Gather all .txt files
    files = list(IMG_SUGGESTIONS_DIR.rglob("*.txt"))
    print(f"found {len(files)} text files.")

    # Session cache for manual replacements to avoid asking for the same term twice
    # Key: search_term, Value: replacement_term (or None to skip)
    manual_decisions = {}

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8")
            original_content = content
            modified = False

            # 1. Apply Auto Replacements
            for search, replace in AUTO_REPLACEMENTS.items():
                if search in content:
                    count = content.count(search)
                    content = content.replace(search, replace)
                    print(f"  [AUTO] Replaced {count}x '{search}' -> '{replace}' in {file_path.name}")
                    modified = True

            # 2. Apply Manual Replacements
            for term in MANUAL_TERMS_TO_FIND:
                if term in content:
                    # Check if we already have a decision for this term
                    if term in manual_decisions:
                        replacement = manual_decisions[term]
                        if replacement:
                            count = content.count(term)
                            content = content.replace(term, replacement)
                            print(f"  [MANUAL-CACHED] Replaced {count}x '{term}' -> '{replacement}' in {file_path.name}")
                            modified = True
                        continue

                    # Found a new term to handle
                    print(f"\n🔍 Found manual term '{term}' in {file_path.name}")
                    # Show context (optional, simple version just shows it was found)
                    
                    user_input = input(f"➡️ Replace '{term}' with (ENTER to skip, 'ALL:replacement' to apply to all): ").strip()

                    if not user_input:
                        print("  Skipped.")
                        manual_decisions[term] = None # Remember to skip
                    elif user_input.lower().startswith("all:"):
                        replacement = user_input[4:]
                        manual_decisions[term] = replacement
                        count = content.count(term)
                        content = content.replace(term, replacement)
                        print(f"  [MANUAL-ALL] Replaced {count}x '{term}' -> '{replacement}'")
                        modified = True
                    else:
                        # Single file replacement (or we could default to asking every time if not ALL)
                        # For simplicity, let's assume if they type a word, they might want to use it again, 
                        # but maybe not *automatically* for every file unless they said ALL.
                        # But the prompt implies "bulk". Let's stick to per-file unless ALL is used.
                        # Actually, let's keep it simple: Input applies to THIS file. 
                        # If they want global, they use the AUTO_REPLACEMENTS dict in code.
                        # BUT, to be friendly, let's ask "Apply to all remaining files?"
                        
                        replacement = user_input
                        count = content.count(term)
                        content = content.replace(term, replacement)
                        print(f"  [MANUAL] Replaced {count}x '{term}' -> '{replacement}'")
                        modified = True
                        
                        # Ask to remember
                        remember = input(f"  Apply '{replacement}' to ALL remaining files for '{term}'? (y/n): ").strip().lower()
                        if remember == 'y':
                            manual_decisions[term] = replacement

            if modified:
                file_path.write_text(content, encoding="utf-8")
                print(f"💾 Saved updates to {file_path.name}")

        except Exception as e:
            print(f"❌ Error processing {file_path.name}: {e}")

    print("\n✅ Done.")

if __name__ == "__main__":
    main()
