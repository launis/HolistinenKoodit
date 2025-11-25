import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

model_name = "gemini-2.5-flash"
print(f"Testing {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say hello", request_options={"timeout": 30})
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")

model_name = "gemini-1.5-flash"
print(f"Testing {model_name}...")
try:
    model = genai.GenerativeModel(model_name)
    response = model.generate_content("Say hello", request_options={"timeout": 30})
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
