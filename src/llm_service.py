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

    def generate_response(self, prompt, model_name="gemini-2.5-flash", validation_fn=None):
        """
        Suorittaa LLM-kutsun retry-logiikalla.
        
        Args:
            prompt (str): Syöte tekoälylle.
            model_name (str): Mallin nimi.
            validation_fn (callable, optional): Funktio, joka ottaa parsitun JSON-objektin 
                                              ja palauttaa True (validi) tai False (epävalidi).
        """
        max_retries = 5
        retry_delay = 2 # sekuntia
        
        import json

        for attempt in range(max_retries):
            try:
                print(f"--- LLM REQUEST START ({model_name}, attempt {attempt+1}/{max_retries}) ---")
                model = genai.GenerativeModel(model_name)
                
                # Konfiguraatio: JSON-pakotus ja suurempi token-raja
                generation_config = genai.types.GenerationConfig(
                    max_output_tokens=8192,
                    response_mime_type="application/json"
                )
                
                # Asetetaan timeout 5 minuutiksi (300s)
                response = model.generate_content(
                    prompt, 
                    generation_config=generation_config,
                    request_options={"timeout": 300}
                )
                print(f"--- LLM REQUEST END ---")
                
                # Tarkista onko vastaus validi ennen .text-ominaisuuden käyttöä
                text_response = ""
                if response.candidates and response.candidates[0].content.parts:
                    text_response = response.text
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
                    
                    # Jos finish_reason on MAX_TOKENS (2), palauta osittainen teksti jos mahdollista
                    if response.candidates and response.candidates[0].finish_reason == 2:
                        print("VAROITUS: Token-raja tuli vastaan. Palautetaan osittainen vastaus.")
                        # Yritä kaivaa teksti parts-kokoelmasta
                        if response.candidates[0].content.parts:
                            text_response = response.candidates[0].content.parts[0].text
                        # Tai response.text jos se toimii
                        try:
                            text_response = response.text
                        except:
                            pass
                    else:
                         raise ValueError(error_msg) # Heitä virhe jotta retry toimii

                # --- VALIDOINTI ---
                cleaned_json_str = self._clean_json_response(text_response)
                
                try:
                    parsed_json = json.loads(cleaned_json_str)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Virheellinen JSON-rakenne: {e}")

                if validation_fn:
                    if not validation_fn(parsed_json):
                        raise ValueError("Vastaus ei läpäissyt skeemavalidointia (validation_fn palautti False).")
                
                # Jos päästiin tänne, kaikki on OK
                return cleaned_json_str

            except Exception as e:
                print(f"VIRHE LLM-kutsussa: {str(e)}")
                if attempt < max_retries - 1:
                    print(f"Yritetään uudelleen {retry_delay}s kuluttua...")
                    time.sleep(retry_delay)
                else:
                    return f"VIRHE LLM-kutsussa (kaikki yritykset epäonnistuivat): {str(e)}"

    def _clean_json_response(self, text):
        """
        Etsii tekstistä ensimmäisen '{' ja viimeisen '}' merkin ja palauttaa niiden välisen sisällön.
        """
        if not text:
            return ""
            
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
            
        return text
