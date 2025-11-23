import google.generativeai as genai
import os
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
        Suorittaa LLM-kutsun.
        """
        try:
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            
            # Tarkista onko vastaus validi ennen .text-ominaisuuden käyttöä
            if response.candidates and response.candidates[0].content.parts:
                return response.text
            else:
                # Kerää debug-tietoa, miksi vastaus on tyhjä
                finish_reason = "Tuntematon"
                if response.candidates:
                    finish_reason = str(response.candidates[0].finish_reason)
                
                feedback = "Ei palautetta"
                if hasattr(response, 'prompt_feedback'):
                    feedback = str(response.prompt_feedback)
                    
                return f"VIRHE: Malli ei palauttanut tekstiä. (Finish Reason: {finish_reason}, Feedback: {feedback})"
                
        except Exception as e:
            return f"VIRHE LLM-kutsussa: {str(e)}"
