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
        self.disabled_models = set()

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
            return ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.5-flash-lite"] # Fallback

    def generate_response(self, prompt, model_name="gemini-2.5-flash", validation_fn=None):
        """
        Suorittaa LLM-kutsun retry-logiikalla ja automaattisella fallbackilla.
        """
        # Määritä kokeiltavat mallit
        models_to_try = [model_name]
        
        # Fallback-logiikka: Jos pyydetään 2.5-flash, varaudu käyttämään 2.0-flashia ja 2.5-flash-litea
        if model_name == "gemini-2.5-flash":
            # Käyttäjän toive: 2) gemini-2.0-flash
            models_to_try.append("gemini-2.0-flash")
            # Käyttäjän toive: 3) gemini-2.5-flash-lite
            models_to_try.append("gemini-2.5-flash-lite")

        max_retries = 5
        retry_delay = 2 # sekuntia
        
        import json
        last_error = None

        for current_model in models_to_try:
            # TARKISTA ONKO MALLI ESTOLISTALLA (QUOTA TÄYNNÄ AIEMMIN)
            if current_model in self.disabled_models:
                print(f"--- OHITETAAN MALLI {current_model} (QUOTA TÄYNNÄ AIEMMIN) ---")
                continue

            print(f"--- KÄYTETÄÄN MALLIA: {current_model} ---")
            
            for attempt in range(max_retries):
                try:
                    print(f"--- LLM REQUEST START ({current_model}, attempt {attempt+1}/{max_retries}) ---")
                    model = genai.GenerativeModel(current_model)
                    
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
                    
                    # Tarkista onko vastaus validi
                    text_response = ""
                    if response.candidates and response.candidates[0].content.parts:
                        text_response = response.text
                    else:
                        # ... (Virheenkäsittely kuten ennen) ...
                        finish_reason = "Tuntematon"
                        if response.candidates:
                            finish_reason = str(response.candidates[0].finish_reason)
                        
                        error_msg = f"VIRHE: Malli ei palauttanut tekstiä. (Finish Reason: {finish_reason})"
                        # Jos token-raja, yritä palauttaa osittainen
                        if response.candidates and response.candidates[0].finish_reason == 2:
                             try: text_response = response.text
                             except: pass
                        
                        if not text_response:
                            raise ValueError(error_msg)

                    # --- VALIDOINTI ---
                    cleaned_json_str = self._clean_json_response(text_response)
                    
                    try:
                        parsed_json = json.loads(cleaned_json_str)
                    except json.JSONDecodeError as e:
                        raise ValueError(f"Virheellinen JSON-rakenne: {e}")

                    if validation_fn:
                        if not validation_fn(parsed_json):
                            raise ValueError("Vastaus ei läpäissyt skeemavalidointia.")
                    
                    # Jos päästiin tänne, onnistui!
                    return cleaned_json_str

                except Exception as e:
                    last_error = e
                    print(f"VIRHE LLM-kutsussa ({current_model}): {str(e)}")
                    
                    # Tarkista onko kyseessä 429 (Rate Limit)
                    is_rate_limit = "429" in str(e) or "Quota exceeded" in str(e)
                    
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        if is_rate_limit:
                            print(f"Rate limit iski. Odotetaan {wait_time} sekuntia...")
                        else:
                            print(f"Yritetään uudelleen {wait_time}s kuluttua...")
                        time.sleep(wait_time)
                    else:
                        print(f"Kaikki yritykset epäonnistuivat mallilla {current_model}.")
            
            # Jos tultiin tänne, mallin kaikki yritykset epäonnistuivat.
            # Jos kyseessä oli Rate Limit, LISÄÄ MALLI ESTOLISTALLE ja kokeile seuraavaa.
            if "429" in str(last_error) or "Quota exceeded" in str(last_error):
                print(f"LISÄTÄÄN {current_model} ESTOLISTALLE (QUOTA TÄYNNÄ).")
                self.disabled_models.add(current_model)
                print(f"Vaihdetaan varamalliin (Fallback)...")
                continue
            else:
                # Jos muu virhe, kannattaako vaihtaa? Usein kyllä.
                print(f"Vakava virhe. Kokeillaan varamallia varmuuden vuoksi...")
                continue

        # Jos kaikki mallit epäonnistuivat
        final_error_msg = f"""
        ============================================================
        VIRHE: KAIKKI TEKOÄLYMALLIT EPÄONNISTUIVAT (QUOTA TÄYNNÄ?)
        ============================================================
        Viimeisin virhe: {last_error}
        
        Tarkista:
        1. Onko Google Cloud -laskutus päällä?
        2. Onko API-quota (Free Tier) ylittynyt tälle päivälle?
        3. Kokeile vaihtaa API-avainta tai odota hetki.
        ============================================================
        """
        return final_error_msg # Palautetaan virheteksti UI:lle (tai heitetään poikkeus)

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
