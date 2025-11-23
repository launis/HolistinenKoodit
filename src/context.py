class AssessmentContext:
    """
    Hallinnoi arvioinnin kontekstia: tiedostoja, tuloksia ja sääntöjä.
    Toimii "Single Source of Truth" datalle prosessin aikana.
    """
    def __init__(self, common_rules, prompt_modules):
        self.common_rules = common_rules if common_rules else ""
        self.prompt_modules = prompt_modules if prompt_modules else {}
        self.files = [] # List of tuples: (filename, content)
        self.results = {} # Dict: phase_id -> result_text

    def add_file(self, filename, content):
        """Lisää tiedoston kontekstiin."""
        self.files.append((filename, content))

    def add_result(self, phase_id, content):
        """Lisää vaiheen tuloksen kontekstiin."""
        self.results[phase_id] = content

    def get_files_text(self):
        """Palauttaa tiedostot muotoiltuna tekstinä."""
        text = ""
        for filename, content in self.files:
            text += f"\n--- TIEDOSTO: {filename} ---\n{content}\n"
        return text

    def get_history_text(self):
        """Palauttaa aiemmat tulokset muotoiltuna tekstinä."""
        text = ""
        if self.results:
            text += "\n\n--- AIEMMAT TULOKSET ---\n"
            for key, val in self.results.items():
                text += f"\n=== TULOS: {key} ===\n{val}\n"
        return text

    def build_prompt(self, phase_key):
        """
        Rakentaa täydellisen kehotteen tietylle vaiheelle.
        """
        # 1. Yleiset säännöt
        prompt = self.common_rules

        # 2. Vaihekohtaiset ohjeet
        if phase_key and phase_key in self.prompt_modules:
            prompt += f"\n\n--- {phase_key} ---\n{self.prompt_modules[phase_key]}"
        else:
            # Jos vaihetta ei löydy, palautetaan virhe (tai käsitellään kutsujassa)
            # Tässä palautetaan pelkkä runko, kutsuja voi tarkistaa
            pass

        # 3. Tiedostot
        prompt += f"\n\n{self.get_files_text()}"

        # 4. Historia
        prompt += self.get_history_text()

        # 5. Lopetus / Tehtävänanto
        prompt += f"\n\n--- SUORITA {phase_key} ---"

        return prompt
