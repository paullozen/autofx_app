"""Process manually added image suggestions and distribute them among profiles."""
from __future__ import annotations

from pathlib import Path
from support_scripts.manifesto import ensure_entry, update_stage
from support_scripts.paths import IMG_SUGGESTIONS_DIR
from profiles import list_profiles, choose_profiles

OUTPUT_DIR = IMG_SUGGESTIONS_DIR


def process_manual_suggestions(base: str, chosen_profiles: list[str]) -> None:
    """Process manually added suggestions (skip OpenAI generation)."""
    ensure_entry(base)
    base_out_dir = OUTPUT_DIR / base
    base_out_dir.mkdir(parents=True, exist_ok=True)
    
    # Look for manual suggestions file
    manual_file = base_out_dir / f"{base}__manual.txt"
    
    if not manual_file.exists():
        print(f"❌ {base}: Manual suggestions file not found: {manual_file}")
        update_stage(base, "suggestions", "error: manual file not found")
        return
    
    update_stage(base, "suggestions", "in_progress")
    
    try:
        # Read manual suggestions
        content = manual_file.read_text(encoding="utf-8")
        
        # EXTRACT SUGGESTIONS
        import re
        
        # Check if explicit "Suggestion:" format is used
        if "Suggestion:" in content:
            # Pattern to match "Suggestion:" followed by everything until the next "Suggestion:" or end
            pattern = r'Suggestion:\s*(.+?)(?=Suggestion:|$)'
            matches = re.findall(pattern, content, re.IGNORECASE | re.DOTALL)
            print(f"ℹ️ {base}: Detected explicit 'Suggestion:' format.")
        else:
            # Assume raw format: each non-empty line is a suggestion
            matches = [line.strip() for line in content.splitlines() if line.strip()]
            print(f"ℹ️ {base}: Detected raw text format. Treating each line as a suggestion.")

        if not matches:
            print(f"❌ {base}: No suggestions found in manual file")
            update_stage(base, "suggestions", "error: no suggestions found")
            return
        
        # Clean and format each suggestion
        scenes = []
        for idx, suggestion_text in enumerate(matches, start=1):
            # Clean the suggestion text
            cleaned = suggestion_text.strip()
            
            # Remove surrounding quotes if present
            if (cleaned.startswith('"') and cleaned.endswith('"')) or \
               (cleaned.startswith("'") and cleaned.endswith("'")):
                cleaned = cleaned[1:-1].strip()
            
            # Replace escaped quotes
            cleaned = cleaned.replace('""', '"')
            
            # Remove extra whitespace and newlines
            cleaned = ' '.join(cleaned.split())
            
            # Add "Suggestion:" prefix back
            final_suggestion = f"Suggestion: {cleaned}"
            
            scenes.append({
                'scene': idx,
                'suggestion': final_suggestion
            })
        
        total = len(scenes)
        print(f"\n📝 {base}: Found {total} suggestions")
        
        # STEP 1: Save consolidated suggestions file for audit
        consolidated_file = base_out_dir / f"{base}_suggestions.txt"
        print(f"\n💾 Saving consolidated file: {consolidated_file.name}")
        
        with open(consolidated_file, "w", encoding="utf-8") as f_consolidated:
            for scene_data in scenes:
                block = [
                    f"Scene {scene_data['scene']}",
                    scene_data['suggestion'],
                    ""
                ]
                f_consolidated.write("\n".join(block) + "\n")
        
        print(f"✅ Consolidated file saved with {total} scenes")
        
        # STEP 2: Distribute scenes among profiles
        print(f"\n📦 Distributing among {len(chosen_profiles)} profile(s)...")
        
        P = len(chosen_profiles)
        scenes_per_profile = total // P
        remainder = total % P
        
        scene_idx = 0
        
        for idx, prof_name in enumerate(chosen_profiles):
            # Calculate how many scenes this profile gets
            # First profiles get one extra scene if there's a remainder
            num_scenes = scenes_per_profile + (1 if idx < remainder else 0)
            
            if num_scenes == 0:
                continue
            
            # Get the subset of scenes for this profile
            subset = scenes[scene_idx : scene_idx + num_scenes]
            start_scene = scenes[scene_idx]['scene']
            end_scene = scenes[scene_idx + num_scenes - 1]['scene']
            
            out_path = base_out_dir / f"{base}__{prof_name}.txt"
            
            print(f"   [{prof_name}] Scenes {start_scene}-{end_scene} ({num_scenes} scenes)")
            
            with open(out_path, "w", encoding="utf-8") as f_out:
                for scene_data in subset:
                    block = [
                        f"Scene {scene_data['scene']}",
                        scene_data['suggestion'],
                        ""
                    ]
                    f_out.write("\n".join(block) + "\n")
            
            scene_idx += num_scenes
        
        update_stage(
            base,
            "suggestions",
            "done",
            extra={
                "mode": "manual",
                "total_suggestions": total,
                "scenes": total,
            },
        )
        print(f"\n✅ {base} → {total} manual suggestions processed successfully")
        print(f"   📄 Consolidated: {consolidated_file.name}")
        print(f"   📦 Distributed among {len(chosen_profiles)} profile(s)")
    
    except Exception as err:
        update_stage(base, "suggestions", f"error: {err}")
        print(f"❌ {base}: {err}")


def main():
    print("\n🎨 MANUAL SUGGESTIONS PROCESSOR\n")
    
    # Find bases with manual suggestion files
    manual_bases = []
    for base_dir in OUTPUT_DIR.iterdir():
        if base_dir.is_dir():
            manual_file = base_dir / f"{base_dir.name}__manual.txt"
            if manual_file.exists():
                manual_bases.append(base_dir.name)
    
    if not manual_bases:
        print("❌ No manual suggestion files found.")
        print(f"   Looking in: {OUTPUT_DIR}")
        return
    
    print(f"📂 Found {len(manual_bases)} base(s) with manual suggestions:")
    for base in manual_bases:
        print(f"   - {base}")
    
    # Choose profiles
    profiles = list_profiles()
    chosen_profiles = choose_profiles(profiles)
    
    # Process each base
    for base in manual_bases:
        process_manual_suggestions(base, chosen_profiles)
    
    print("\n✅ Finished processing manual suggestions.")


if __name__ == "__main__":
    main()
