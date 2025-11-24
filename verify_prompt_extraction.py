from src.processor import AIProcessor
import os

def verify_prompt_extraction():
    processor = AIProcessor()
    prompt_file = "Pääarviointikehote.docx"
    
    if not os.path.exists(prompt_file):
        print(f"ERROR: {prompt_file} not found.")
        return

    print(f"Reading {prompt_file}...")
    common_rules, phases = processor.parse_prompt_modules(prompt_file)
    
    print(f"Common Rules Length: {len(common_rules)}")
    print(f"Phases found: {list(phases.keys())}")
    
    target_phase = "VAIHE 4"
    if target_phase in phases:
        content = phases[target_phase]
        with open("phase_4_prompt_dump.txt", "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Phase 4 content written to phase_4_prompt_dump.txt ({len(content)} chars)")
    else:
        print(f"\nERROR: {target_phase} NOT FOUND in phases.")
        # Print all keys to see what was found
        for key in phases:
            print(f"Found phase: '{key}'")

if __name__ == "__main__":
    verify_prompt_extraction()
