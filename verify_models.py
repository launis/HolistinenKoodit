import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

target_models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-flash-002"
]

print("Checking available models...")
try:
    available_models = [m.name.replace("models/", "") for m in genai.list_models()]
    
    print("\n--- RESULTS ---")
    for target in target_models:
        if target in available_models:
            print(f"[OK] {target} exists.")
        else:
            print(f"[FAIL] {target} NOT FOUND.")
            
    print("\n--- ALL AVAILABLE MODELS ---")
    for m in available_models:
        print(m)
        
except Exception as e:
    print(f"Error listing models: {e}")
