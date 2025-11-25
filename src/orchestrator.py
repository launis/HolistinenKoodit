from config import PHASES
import time
from report_generator import ReportGenerator

class Orchestrator:
    """
    Prosessinohjauskerros: Määrittelee työnkulun ja ketjuttaa datan.
    """
    def __init__(self, llm_service, data_handler):
        self.llm_service = llm_service
        self.data_handler = data_handler
        self.report_generator = ReportGenerator()
        self.results = {}

    def get_phases(self):
        return PHASES

    def run_phase(self, phase_id, context, model_name):
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

        # Tallenna tulos kontekstiin ja lokaaliin välimuistiin (jos tarpeen)
        # Käytetään phase_keytä (esim. "VAIHE 1") avaimena, jotta malli ymmärtää kontekstin paremmin
        context.add_result(phase_key, cleaned_result)
        self.results[phase_id] = cleaned_result
        
        return cleaned_result

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

    def run_mode(self, mode_name, context, model_name):
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
        for phase_id in phase_ids:
            result = self.run_phase(phase_id, context, model_name)
            results[phase_id] = result
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
