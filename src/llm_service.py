import google.generativeai as genai
import os
import time
from dotenv import load_dotenv

class LLMService:
    """
    Infrastruktuurikerros: Hoitaa yhteyden Gemini-tekoälyyn.
    """
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY puuttuu .env-tiedostosta.")
        genai.configure(api_key=api_key)

    def get_available_models(self):
        """Hakee saatavilla olevat mallit."""
        try:
            models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name.replace("models/", ""))
            return models
        except Exception as e:
            print(f"Virhe mallien hakemisessa: {e}")
            return ["gemini-2.5-flash", "gemini-1.5-flash"] # Fallback

    def generate_response(self, prompt, model_name="gemini-2.5-flash"):
        """
        Suorittaa LLM-kutsun retry-logiikalla.
        """
        max_retries = 3
        retry_delay = 2 # sekuntia
        
        for attempt in range(max_retries):
            try:
                print(f"--- LLM REQUEST START ({model_name}, attempt {attempt+1}/{max_retries}) ---")
                model = genai.GenerativeModel(model_name)
                # Asetetaan timeout 5 minuutiksi (300s)
                response = model.generate_content(prompt, request_options={"timeout": 300})
                print(f"--- LLM REQUEST END ---")
                
                # Tarkista onko vastaus validi ennen .text-ominaisuuden käyttöä
                if response.candidates and response.candidates[0].content.parts:
                    return response.text
                else:
                    # Kerää debug-tietoa
                    finish_reason = "Tuntematon"
                    candidate_debug = "Ei kandidaatteja"
                    if response.candidates:
                        finish_reason = str(response.candidates[0].finish_reason)
                        candidate_debug = str(response.candidates[0])
                    
                    feedback = "Ei palautetta"
                    if hasattr(response, 'prompt_feedback'):
                        feedback = str(response.prompt_feedback)
                        
                    error_msg = f"VIRHE: Malli ei palauttanut tekstiä. (Finish Reason: {finish_reason})\nDebug: {candidate_debug}\nFeedback: {feedback}"
                    print(error_msg)
                    
                    # Jos finish_reason on STOP mutta sisältö tyhjä, se on outoa. Yritetään uudelleen.
                    # Jos finish_reason on SAFETY, retry ei ehkä auta, mutta kokeillaan.
                    if attempt < max_retries - 1:
                        print(f"Yritetään uudelleen {retry_delay}s kuluttua...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        return error_msg
                    
            except Exception as e:
                print(f"VIRHE LLM-kutsussa: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Yritetään uudelleen {retry_delay}s kuluttua...")
                    time.sleep(retry_delay)
                else:
                    return f"VIRHE LLM-kutsussa (kaikki yritykset epäonnistuivat): {str(e)}"
