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

        # Suorita LLM-kutsu
        result = self.llm_service.generate_response(final_prompt, model_name)
        
        # Tallenna tulos kontekstiin ja lokaaliin välimuistiin (jos tarpeen)
        # Käytetään phase_keytä (esim. "VAIHE 1") avaimena, jotta malli ymmärtää kontekstin paremmin
        context.add_result(phase_key, result)
        self.results[phase_id] = result
        
        return result

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
        
        # ERIKOISKÄSITTELY: Moodi C (Vaihe 8 + 9)
        # Vaihe 9 on Python-generaattori, joten sitä ei voi yhdistää LLM-promptiin.
        if mode_name == "MOODI_C":
            results = {}
            for phase_id in phase_ids:
                result = self.run_phase(phase_id, context, model_name)
                results[phase_id] = result
            return results

        # MOODIT A ja B: Yhdistetty ajo
        # 1. Kerää vaiheiden avaimet (esim. "VAIHE 1", "VAIHE 2")
        phase_keys = []
        for pid in phase_ids:
            p = next((x for x in PHASES if x["id"] == pid), None)
            if p: phase_keys.append(p["phase_key"])
            
        # 2. Rakenna yksi iso prompt
        combined_prompt = context.build_combined_prompt(phase_keys)
        
        # 3. Aja LLM
        result_text = self.llm_service.generate_response(combined_prompt, model_name)
        
        # 4. Tallenna tulos
        # Tallennetaan koko moodin tulos yhtenä könttinä kontekstiin
        # Tämä toimii "Container"-logiikalla: seuraava moodi saa koko edellisen moodin tulosteen syötteenä
        context.add_result(mode_name, result_text)
        
        # Palautetaan tulos sanakirjana (yksi avain koko moodille)
        return {mode_name: result_text}

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
