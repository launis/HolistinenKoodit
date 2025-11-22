from src.processor import AIProcessor

def verify_model_fallback():
    print("Verifying model fallback logic...")
    processor = AIProcessor()
    available_models = processor.get_available_models()
    print(f"Available models: {available_models}")
    
    model_b_name = "gemini-1.5-flash"
    model_a_name = "gemini-pro"
    
    if model_b_name in available_models:
        selected_model = model_b_name
        print(f"Logic check: Found {model_b_name}, selected it.")
    else:
        selected_model = model_a_name
        print(f"Logic check: Did NOT find {model_b_name}, fell back to {model_a_name}.")
        
    if selected_model in available_models:
        print("SUCCESS: Selected model is valid.")
    else:
        print("WARNING: Selected model might be invalid if API key is missing.")

if __name__ == "__main__":
    verify_model_fallback()
