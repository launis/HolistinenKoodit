import os
from src.data_handler import DataHandler

def inspect():
    dh = DataHandler()
    prompt_path = os.path.join(os.getcwd(), "Pääarviointikehote.docx")
    
    if not os.path.exists(prompt_path):
        print(f"File not found: {prompt_path}")
        return

    print(f"Reading: {prompt_path}")
    common, phases = dh.parse_prompt_modules(prompt_path)
    
    print("\n=== COMMON RULES ===")
    print(common[:500] + "..." if len(common) > 500 else common)
    
    print("\n=== PHASES FOUND ===")
    print(list(phases.keys()))
    
    if "VAIHE 8" in phases:
        print("\n=== VAIHE 8 CONTENT ===")
        print(phases["VAIHE 8"])
        
    if "VAIHE 9" in phases:
        print("\n=== VAIHE 9 CONTENT ===")
        print(phases["VAIHE 9"])

if __name__ == "__main__":
    inspect()
