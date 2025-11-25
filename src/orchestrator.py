from config import PHASES
import time
from report_generator import ReportGenerator
from search_service import SearchService
from security_validator import SecurityValidator
import json

class Orchestrator:
    """
    Prosessinohjauskerros: Määrittelee työnkulun ja ketjuttaa datan.
    """
    def __init__(self, llm_service, data_handler):
        self.llm_service = llm_service
        self.data_handler = data_handler
        self.report_generator = ReportGenerator()
        self.search_service = SearchService()
        self.security_validator = SecurityValidator()
        self.results = {}

    def get_phases(self):
        return PHASES

    def run_phase(self, phase_id, context, model_name, save_dataset=False):
        """
        Suorittaa yhden vaiheen käyttäen AssessmentContextia.
        """
        # ERIKOISKÄSITTELY: Vaihe 9 (Raportointi) hoidetaan Pythonilla
        if phase_id == "phase_9":
            result = self.report_generator.generate_report(context)
            context.add_result("VAIHE 9", result)
            self.results[phase_id] = result
            return result

        # Etsi vaiheen tiedot
        phase = next((p for p in PHASES if p["id"] == phase_id), None)
        if not phase:
            return f"VIRHE: Vaihetta {phase_id} ei löydy."

        phase_key = phase["phase_key"]
        
        # Rakenna prompt context-objektin avulla
        final_prompt = context.build_prompt(phase_key)
        
        # Tarkista onko vaihe olemassa (build_prompt ei heitä virhettä, mutta tarkistus on hyvä)
        if phase_key not in context.prompt_modules:
             return f"VAROITUS: Vaihetta '{phase_key}' ei löytynyt kehotteesta."

        # --- PYTHON-TURVALLISUUSTARKISTUS (Pre-Phase 1) ---
        if phase_id == "phase_1":
            print("--- SUORITETAAN PYTHON-TURVALLISUUSTARKISTUS ---")
            security_report = self.security_validator.validate_all(context)
            
            # 1. Kriittiset uhkat -> Pysäytä heti
            if security_report["security_threats"]:
                threats_str = "\n".join(security_report["security_threats"])
                return json.dumps({
                    "security_check": {
                        "uhka_havaittu": True,
                        "adversariaalinen_simulaatio_tulos": f"PYTHON-VARTIJA HAVAITSI UHAN:\n{threats_str}",
                        "riski_taso": "KORKEA"
                    },
                    "data": {},
                    "metodologinen_loki": "Prosessi pysäytetty Python-vartijan toimesta ennen LLM-kutsua."
                }, indent=2)

            # 2. Injektoi löydökset promptiin (jos on PII tai muita huomioita)
            findings_text = ""
            if security_report["pii_findings"]:
                findings_text += "\n\nHUOMIO: Python-skanneri löysi mahdollisia henkilötietoja:\n" + "\n".join(security_report["pii_findings"])
            if security_report["validation_issues"]:
                findings_text += "\n\nHUOMIO: Tiedostovalidoinnin huomiot:\n" + "\n".join(security_report["validation_issues"])
            
            # 3. SUORITA SANITOINTI (Normalisointi & Anonymisointi)
            sanitization_msg = self.security_validator.sanitize_all(context)
            print(f"--- {sanitization_msg} ---")
            
            if findings_text:
                final_prompt += findings_text
                final_prompt += "\n\nHUOMIO: Tiedostot on automaattisesti normalisoitu ja PII-anonymisoitu Python-skriptillä."
                print("Turvallisuuslöydökset lisätty promptiin.")

        # --- FAKTANTARKISTUS (Pre-Phase 7) ---
        if phase_id == "phase_7" and self.search_service.api_key and self.search_service.cx:
            print("--- KÄYNNISTETÄÄN FAKTANTARKISTUS (Google Search) ---")
            try:
                # 1. Etsi väitteitä (käytetään kevyttä LLM-kutsua)
                claims_prompt = f"""
                Tehtäväsi on poimia seuraavasta tekstistä 3 keskeisintä faktaväitettä, jotka on syytä tarkistaa ulkoisesta lähteestä.
                Keskity väitteisiin, jotka koskevat vuosilukuja, tapahtumia, henkilöitä tai tieteellisiä faktoja.
                
                Teksti (Lopputuote/Reflektio):
                {context.get_file_content("Lopputuote.pdf")[:5000]} 
                
                Palauta vain JSON-lista merkkijonoista: ["Väite 1", "Väite 2", "Väite 3"]
                """
                claims_json = self.llm_service.generate_response(claims_prompt, model_name="gemini-2.5-flash") # Käytä nopeaa mallia
                
                # Robust JSON parsing (käsittele myös 'single quotes')
                import ast
                try:
                    claims = json.loads(self._clean_json_response(claims_json))
                except json.JSONDecodeError:
                    try:
                        # Yritä Python-syntaksilla (jos malli palautti ['Väite 1'])
                        claims = ast.literal_eval(self._clean_json_response(claims_json))
                    except:
                        print(f"Virhe faktantarkistusprosessissa: Ei voitu parsia JSONia: {claims_json}")
                        claims = []
                
                if isinstance(claims, list):
                    search_results_text = "\n\nULKOISEN FAKTANTARKISTUKSEN TULOKSET (Google Search):\n"
                    for claim in claims[:3]: # Max 3 väitettä
                        print(f"Tarkistetaan väite: {claim}")
                        results, error = self.search_service.search(claim, num_results=2)
                        if error:
                            search_results_text += f"- Väite: {claim}\n  VIRHE: {error}\n"
                        elif results:
                            search_results_text += f"- Väite: {claim}\n"
                            for res in results:
                                search_results_text += f"  * Lähde: {res['title']} ({res['link']})\n    Snippet: {res['snippet']}\n"
                        else:
                            search_results_text += f"- Väite: {claim}\n  Ei hakutuloksia.\n"
                    
                    # Injektoi tulokset promptiin
                    final_prompt += search_results_text
                    print("Faktantarkistus valmis. Tulokset lisätty promptiin.")
            except Exception as e:
                print(f"Virhe faktantarkistusprosessissa: {e}")

        # Määritä validointifunktio, jos vaiheella on schema
        validation_fn = None
        required_keys = []
        if "schema" in phase:
             # Extract top-level keys from the schema for validation
             required_keys = list(phase["schema"].get("properties", {}).keys())

        if required_keys:
            def validate_schema(data):
                missing_keys = [key for key in required_keys if key not in data]
                if missing_keys:
                    print(f"SCHEMA VALIDATION FAILED for {phase_id}: Missing keys {missing_keys}")
                    return False
                return True
            validation_fn = validate_schema

        # Suorita LLM-kutsu
        result = self.llm_service.generate_response(final_prompt, model_name, validation_fn=validation_fn)
        
        # Puhdista JSON-vastaus (poista "Here is the JSON" -tyyppiset höpinät)
        cleaned_result = self._clean_json_response(result)
        
        # KÄSITTELE PLACEHOLDERIT (VAIHE 1 OPTIMOINTI)
        # Jos vastaus sisältää {{FILE: ...}}, korvaa se tiedoston sisällöllä
        if "{{FILE:" in cleaned_result:
            cleaned_result = self._inject_file_content(cleaned_result, context)

        # PÄIVITÄ AIKALEIMA (KORJATTU)
        try:
            data = json.loads(cleaned_result)
            if isinstance(data, dict):
                # Varmista että metadata-objekti on olemassa
                if "metadata" not in data:
                    data["metadata"] = {}
                
                # Aseta nykyinen aika
                from datetime import datetime
                current_time = datetime.now().isoformat()
                data["metadata"]["luontiaika"] = current_time
                
                # Päivitä cleaned_result
                cleaned_result = json.dumps(data, indent=2, ensure_ascii=False)
        except Exception as e:
            # Jos ei ole validia JSONia, ei voida päivittää aikaleimaa
            pass

        # Tallenna tulos kontekstiin ja lokaaliin välimuistiin (jos tarpeen)
        # Käytetään phase_keytä (esim. "VAIHE 1") avaimena, jotta malli ymmärtää kontekstin paremmin
        context.add_result(phase_key, cleaned_result)
        self.results[phase_id] = cleaned_result
        
        if save_dataset:
            self._save_to_dataset(phase_id, cleaned_result)

        return cleaned_result

    def _save_to_dataset(self, phase_id, content):
        """
        Tallentaa vaiheen tuloksen dataset/ -kansioon tutkimuskäyttöä varten (Luku 6.2).
        """
        import os
        from datetime import datetime
        
        dataset_dir = os.path.join(os.getcwd(), "dataset")
        if not os.path.exists(dataset_dir):
            os.makedirs(dataset_dir)
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{phase_id}.json"
        filepath = os.path.join(dataset_dir, filename)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"DATASET: Tallennettu {filename}")
        except Exception as e:
            print(f"DATASET VIRHE: Ei voitu tallentaa {filename}: {e}")

    def _clean_json_response(self, text):
        """
        Etsii tekstistä ensimmäisen '{' ja viimeisen '}' merkin ja palauttaa niiden välisen sisällön.
        Tämä poistaa mallin mahdolliset "Here is the JSON..." -alku/lopputekstit.
        """
        if not text:
            return ""
            
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
            
        return text

    def _inject_file_content(self, text, context):
        """
        Korvaa {{FILE: tiedostonimi}} -placeholderit tiedoston sisällöllä.
        """
        import re
        
        # Etsi kaikki placeholderit
        # Oletetaan muoto: "{{FILE: tiedostonimi}}" tai '{{FILE: tiedostonimi}}'
        pattern = re.compile(r'\{\{FILE:\s*(.*?)\}\}')
        
        def replace_match(match):
            filename = match.group(1).strip()
            # Etsi tiedosto kontekstista
            # context.files on lista (filename, content)
            for fname, content in context.files:
                # Yksinkertainen vertailu (voi vaatia tarkempaa logiikkaa jos polkuja)
                if fname == filename or fname.endswith(filename) or filename in fname:
                    # JSON-escapeeraus on tärkeää!
                    # Mutta jos korvaamme suoraan tekstissä, meidän pitää olla varovaisia JSON-rakenteen kanssa.
                    # Jos placeholder on JSON-stringin sisällä, meidän pitää escapeerata sisältö.
                    # Tässä oletetaan että placeholder on "value": "{{FILE: ...}}"
                    # Joten palautamme sisällön JSON-escapeerattuna (mutta ilman lainausmerkkejä, koska ne ovat jo siellä?)
                    # EI, regex korvaa vain {{FILE: ...}} osan.
                    # Joten meidän pitää palauttaa sisältö escapeerattuna.
                    import json
                    # json.dumps lisää lainausmerkit alkuun ja loppuun, poistetaan ne
                    escaped_content = json.dumps(content)
                    if escaped_content.startswith('"') and escaped_content.endswith('"'):
                        escaped_content = escaped_content[1:-1]
                    return escaped_content
            
            return f"[TIEDOSTOA {filename} EI LÖYTYNYT]"

        return pattern.sub(replace_match, text)

    def run_mode(self, mode_name, context, model_name, critic_model_name=None, save_dataset=False):
        """
        Suorittaa tietyn moodin (A, B tai C).
        - Moodit A ja B ajetaan yhtenä isona promptina.
        - Moodi C ajetaan sekventiaalisesti (koska Vaihe 9 on Python-koodia).
        """
        from config import EXECUTION_MODES, PHASES
        
        if mode_name not in EXECUTION_MODES:
            return f"VIRHE: Tuntematon moodi {mode_name}"
            
        phase_ids = EXECUTION_MODES[mode_name]
        
        # KAIKKI MOODIT: Ajetaan vaiheet sekventiaalisesti
        # Tämä on varmempi tapa välttää token-rajat ja varmistaa että jokainen vaihe saa huomiota.
        results = {}
        import json
        
        # Jos critic_model_name ei ole annettu, käytä päämallia
        if not critic_model_name:
            critic_model_name = model_name
        
        for phase_id in phase_ids:
            # Valitse malli
            current_model = model_name
            if phase_id in ["phase_4", "phase_5", "phase_6", "phase_7"]:
                current_model = critic_model_name
                
            result = self.run_phase(phase_id, context, current_model, save_dataset=save_dataset)
            results[phase_id] = result
            
            # EHDOLINEN LOGIIKKA: Jos Vaihe 1 löytää uhan, pysäytä prosessi.
            if phase_id == "phase_1":
                try:
                    data = json.loads(result)
                    # Tarkista onko uhka havaittu (huomioi boolean tai string "true"/"false")
                    security = data.get("security_check", {})
                    uhka = security.get("uhka_havaittu", False)
                    
                    if uhka is True or str(uhka).lower() == "true":
                        print(f"!!! TURVALLISUUSUHKA HAVAITTU VAIHEESSA 1. PYSÄYTETÄÄN PROSESSI. !!!")
                        # Lisää tieto tuloksiin jotta UI voi näyttää sen
                        results["STOPPED_EARLY"] = "Turvallisuusuhka havaittu. Prosessi keskeytetty."
                        break
                except Exception as e:
                    print(f"Varoitus: Ei voitu tarkistaa turvallisuusuhkaa JSONista: {e}")

            # LASKENTALOGIIKKA: Vaihe 8 (Pisteytys)
            if phase_id == "phase_8":
                try:
                    data = json.loads(result)
                    pisteet = data.get("pisteet", {})
                    
                    # Hae arvosanat (default 0 jos puuttuu)
                    s1 = pisteet.get("analyysi_ja_prosessi", {}).get("arvosana", 0)
                    s2 = pisteet.get("arviointi_ja_argumentaatio", {}).get("arvosana", 0)
                    s3 = pisteet.get("synteesi_ja_luovuus", {}).get("arvosana", 0)
                    
                    # Varmista että ovat numeroita
                    try:
                        s1 = int(s1)
                        s2 = int(s2)
                        s3 = int(s3)
                    except:
                        s1 = s2 = s3 = 0
                        
                    total_score = s1 + s2 + s3
                    average_score = round(total_score / 3, 2)
                    
                    # Lisää laskettu data JSONiin
                    data["python_calculated_scores"] = {
                        "total": total_score,
                        "average": average_score,
                        "breakdown": [s1, s2, s3]
                    }
                    
                    # Päivitä tulos
                    updated_result = json.dumps(data, indent=2, ensure_ascii=False)
                    results[phase_id] = updated_result
                    context.add_result(phase_id, updated_result) # Päivitä myös kontekstiin
                    
                    print(f"PYTHON LASKI PISTEET: Yhteensä {total_score}, Keskiarvo {average_score}")
                    
                except Exception as e:
                    print(f"Varoitus: Ei voitu laskea pisteitä JSONista: {e}")

        return results

    def run_agent(self, agent_config, uploaded_files, model_name):
        """
        Suorittaa yksittäisen agentin ajon.
        """
        # 1. Lue tiedostojen sisältö
        files_content = ""
        for uploaded_file in uploaded_files:
            content = self.data_handler.read_file_content(uploaded_file)
            files_content += f"\\n--- TIEDOSTO: {uploaded_file.name} ---\\n{content}\\n"

        # 2. Rakenna lopullinen kehote
        prompt_template = agent_config.get("prompt_template", "")
        final_prompt = prompt_template.replace("{files}", files_content)
        
        # 3. Kutsu LLM-palvelua
        return self.llm_service.generate_response(final_prompt, model_name)
