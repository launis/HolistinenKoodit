class AssessmentContext:
    """
    Hallinnoi arvioinnin kontekstia: tiedostoja, tuloksia ja sääntöjä.
    Toimii "Single Source of Truth" datalle prosessin aikana.
    """
    
    # Määritellään riippuvuudet: Mitä aiempia vaiheita kukin vaihe tarvitsee?
    # Tämä vähentää token-määrää merkittävästi jättämällä turhan historian pois.
    PHASE_DEPENDENCIES = {
        "VAIHE 1": [], # Ei riippuvuuksia
        "VAIHE 2": ["VAIHE 1"],
        "VAIHE 3": ["VAIHE 2", "VAIHE 1"],
        "VAIHE 4": ["VAIHE 3", "VAIHE 2", "VAIHE 1"],
        "VAIHE 5": ["VAIHE 3", "VAIHE 2", "VAIHE 1"],
        "VAIHE 6": ["VAIHE 3", "VAIHE 2", "VAIHE 1"],
        "VAIHE 7": ["VAIHE 3", "VAIHE 2", "VAIHE 1"],
        "VAIHE 8": ["VAIHE 7", "VAIHE 6", "VAIHE 5", "VAIHE 4", "VAIHE 3", "VAIHE 2", "VAIHE 1"],
        "VAIHE 9": ["VAIHE 8", "VAIHE 7", "VAIHE 6", "VAIHE 5", "VAIHE 4", "VAIHE 3", "VAIHE 2", "VAIHE 1"]
    }

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

    def get_files_text(self, phase_key=None):
        """
        Palauttaa tiedostot muotoiltuna tekstinä.
        OPTIMOINTI: Vain Vaiheet 1 ja 2 tarvitsevat alkuperäiset tiedostot.
        Muut vaiheet käyttävät aiempien vaiheiden (esim. VAIHE 1) tuottamaa dataa.
        """
        # Jos phase_keytä ei anneta, palauta kaikki (esim. debuggausta varten)
        if phase_key is None:
            return self._format_all_files()
            
        # Vain Vaihe 1 ja 2 tarvitsevat raakatiedostot
        # Myös Moodi A (joka alkaa Vaiheesta 1) tarvitsee ne
        if phase_key in ["VAIHE 1", "VAIHE 2", "MOODI_A"]:
            return self._format_all_files()
            
        return ""

    def _format_all_files(self):
        text = ""
        for filename, content in self.files:
            text += f"\\n--- TIEDOSTO: {filename} ---\\n{content}\\n"
        return text

    def get_history_text(self, phase_key=None):
        """
        Palauttaa aiemmat tulokset muotoiltuna tekstinä.
        OPTIMOINTI: Palauttaa vain relevantin historian riippuvuuksien perusteella.
        """
        text = ""
        if not self.results:
            return text

        text += "\\n\\n--- AIEMMAT TULOKSET ---\\n"
        
        # Jos phase_key on annettu, suodata riippuvuuksien mukaan
        if phase_key and phase_key in self.PHASE_DEPENDENCIES:
            dependencies = self.PHASE_DEPENDENCIES[phase_key]
            found_any = False
            for dep in dependencies:
                # Tarkista onko riippuvuus olemassa tuloksissa
                # Huom: Tulokset voivat olla tallennettu eri avaimilla (esim. "VAIHE 1" tai "phase_1")
                # Yritetään löytää oikea
                content = self.results.get(dep)
                if content:
                    text += f"\\n=== TULOS: {dep} ===\\n{content}\\n"
                    found_any = True
            
            # Jos ei löytynyt mitään riippuvuuksia, mutta tuloksia on,
            # saatetaan olla tilanteessa jossa ajetaan Moodia (esim. Moodi B tarvitsee Moodi A:n tulokset)
            if not found_any and phase_key.startswith("MOODI"):
                # Moodeille palautetaan kaikki aiemmat tulokset varmuuden vuoksi
                for key, val in self.results.items():
                    text += f"\\n=== TULOS: {key} ===\\n{val}\\n"
        else:
            # Jos ei phase_keytä (tai tuntematon), palauta kaikki (turvallinen oletus)
            for key, val in self.results.items():
                text += f"\\n=== TULOS: {key} ===\\n{val}\\n"
                
        return text

    def build_prompt(self, phase_key):
        """
        Rakentaa täydellisen kehotteen tietylle vaiheelle.
        """
        # 1. Yleiset säännöt (Nyt vain OSA 1-5, ei koko dokumentti!)
        prompt = self.common_rules

        # 2. Vaihekohtaiset ohjeet
        if phase_key and phase_key in self.prompt_modules:
            prompt += f"\\n\\n--- {phase_key} ---\\n{self.prompt_modules[phase_key]}"
        else:
            pass

        # 3. Tiedostot (Vain jos tarpeen)
        prompt += f"\\n\\n{self.get_files_text(phase_key)}"

        # 4. Historia (Vain relevantit)
        prompt += self.get_history_text(phase_key)

        # 5. Lopetus / Tehtävänanto
        prompt += f"\\n\\n--- SUORITA {phase_key} ---"
        
        # HACK: Varmista että Vaihe 9 sisällyttää pisteet
        if phase_key == "VAIHE 9":
            prompt += "\\n\\nTÄRKEÄÄ: Sinun TÄYTYY sisällyttää raporttiin VAIHEEN 8 antamat pisteet selkeänä taulukkona tai listana. Älä jätä niitä pois."

        return prompt

    def build_combined_prompt(self, phase_keys):
        """
        Rakentaa yhdistetyn kehotteen usealle vaiheelle (esim. Moodi A: Vaiheet 1-3).
        """
        # 1. Yleiset säännöt
        prompt = self.common_rules
        
        # 2. Vaihekohtaiset ohjeet (yhdistettynä)
        prompt += "\\n\\n--- SUORITETTAVAT VAIHEET ---\\n"
        prompt += "Sinun tulee suorittaa seuraavat vaiheet yhtenäisenä prosessina. Tulosta jokaisen vaiheen lopputulos omassa selkeässä lohkossaan.\\n"
        
        for key in phase_keys:
            if key in self.prompt_modules:
                prompt += f"\\n\\n=== OHJEET: {key} ===\\n{self.prompt_modules[key]}"
        
        # 3. Tiedostot (Moodi A tarvitsee tiedostot)
        # Päätellään tarve ensimmäisestä vaiheesta
        first_phase = phase_keys[0] if phase_keys else None
        # Jos ensimmäinen vaihe on VAIHE 1, tarvitaan tiedostot
        if first_phase == "VAIHE 1":
            prompt += f"\\n\\n{self.get_files_text('VAIHE 1')}"
        
        # 4. Historia
        # Moodeissa historia on monimutkaisempi, otetaan kaikki varmuuden vuoksi
        # tai viimeisimmän vaiheen riippuvuudet
        prompt += self.get_history_text()
        
        # 5. Lopetus
        prompt += "\\n\\n--- TEHTÄVÄNANTO ---\\n"
        prompt += "Suorita yllä määritellyt vaiheet järjestyksessä. Erottele vastaukset selkeästi otsikoilla (esim. '=== TULOS: VAIHE X ===')."
        
        return prompt
