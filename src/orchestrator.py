from config import PHASES
import time

class Orchestrator:
    """
    Prosessinohjauskerros: Määrittelee työnkulun ja ketjuttaa datan.
    """
    def __init__(self, llm_service, data_handler):
        self.llm_service = llm_service
        self.data_handler = data_handler
        self.results = {}

    def get_phases(self):
        return PHASES

    def run_phase(self, phase_id, context, model_name):
        """
        Suorittaa yhden vaiheen käyttäen AssessmentContextia.
        """
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
        final_prompt = prompt_template.replace("{files}", files_content)
        
        # 3. Kutsu LLM-palvelua
        return self.llm_service.generate_response(final_prompt, model_name)
