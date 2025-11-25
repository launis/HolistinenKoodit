import re

class SecurityValidator:
    """
    Hoitaa tietoturvatarkistukset ja syötteen validoinnin Python-tasolla.
    Tämä vähentää LLM:n kuormaa ja parantaa turvallisuutta deterministisillä säännöillä.
    """

    def __init__(self):
        # Regex-mallit PII-tunnistukseen
        self.pii_patterns = {
            "EMAIL": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "PHONE": re.compile(r'\b(?:(?:\+|00)358|0)\s*(?:\d\s*){4,12}\b'), # Yksinkertaistettu suomalainen numero
            "HETU": re.compile(r'\b\d{6}[-+A]\d{3}[0-9A-FHJ-NPR-Y]\b') # Suomalainen henkilötunnus
        }

        # Regex-mallit Prompt Injection -tunnistukseen (englanti ja suomi)
        self.injection_patterns = [
            re.compile(r'ignore previous instructions', re.IGNORECASE),
            re.compile(r'ohita aiemmat ohjeet', re.IGNORECASE),
            re.compile(r'system override', re.IGNORECASE),
            re.compile(r'järjestelmän ohitus', re.IGNORECASE),
            re.compile(r'you are now', re.IGNORECASE),
            re.compile(r'olet nyt', re.IGNORECASE),
            re.compile(r'delete all files', re.IGNORECASE),
            re.compile(r'poista kaikki tiedostot', re.IGNORECASE)
        ]

    def normalize_text(self, text):
        """
        Normalisoi tekstin: UTF-8 (oletus Pythonissa), älykkäät lainausmerkit, kontrollimerkit.
        """
        if not text:
            return ""
        
        # 1. Älykkäät lainausmerkit
        text = text.replace('”', '"').replace('’', "'").replace('“', '"').replace('‘', "'")
        
        # 2. Kontrollimerkit (säilytä rivinvaihdot ja tabit)
        # Yksinkertainen tapa: poista merkit jotka eivät ole tulostettavia tai whitespacea
        # Mutta Pythonin isprintable() hylkää rivinvaihdot, joten tehdään salliva filtteri
        return "".join(ch for ch in text if ch.isprintable() or ch in '\n\r\t')

    def redact_pii(self, text):
        """
        Korvaa tunnistetut PII-tiedot [PII_REDACTED]-merkinnällä.
        """
        if not text:
            return ""
            
        for pii_type, pattern in self.pii_patterns.items():
            text = pattern.sub(f"[PII_REDACTED_{pii_type}]", text)
            
        return text

    def sanitize_all(self, context):
        """
        Suorittaa normalisoinnin ja anonymisoinnin kaikille tiedostoille.
        MUOKKAA context.files -listaa suoraan!
        """
        new_files = []
        for filename, content in context.files:
            # 1. Normalisointi
            normalized = self.normalize_text(content)
            
            # 2. Anonymisointi
            redacted = self.redact_pii(normalized)
            
            new_files.append((filename, redacted))
        
        context.files = new_files
        return "Tiedostot normalisoitu ja anonymisoitu."

    def scan_for_pii(self, text):
        """
        Etsii tekstistä henkilötietoja (PII).
        Palauttaa listan löydöksistä: [{"type": "EMAIL", "value": "..."}]
        """
        findings = []
        if not text:
            return findings

        for pii_type, pattern in self.pii_patterns.items():
            matches = pattern.findall(text)
            for match in matches:
                findings.append({
                    "type": pii_type,
                    "value": match, # Huom: Oikeassa tuotannossa tämä pitäisi maskata!
                    "risk": "HIGH"
                })
        
        return findings

    def detect_prompt_injection(self, text):
        """
        Etsii tekstistä adversarial prompt -kuvioita.
        Palauttaa listan löydöksistä.
        """
        findings = []
        if not text:
            return findings

        for pattern in self.injection_patterns:
            if pattern.search(text):
                findings.append({
                    "type": "PROMPT_INJECTION",
                    "pattern": pattern.pattern,
                    "risk": "CRITICAL"
                })
        
        return findings

    def validate_file_content(self, filename, content):
        """
        Tarkistaa tiedoston sisällön perusvaliditeetin.
        """
        issues = []
        
        # 1. Tyhjä tiedosto
        if not content or len(content.strip()) == 0:
            issues.append(f"Tiedosto {filename} on tyhjä.")
            return issues

        # 2. Epäilyttävän lyhyt (esim. pelkkä otsikko)
        if len(content) < 50:
            issues.append(f"Tiedosto {filename} on epäilyttävän lyhyt ({len(content)} merkkiä).")

        return issues

    def validate_all(self, context):
        """
        Suorittaa kaikki tarkistukset kaikille kontekstin tiedostoille.
        Palauttaa raportin löydöksistä.
        """
        report = {
            "pii_findings": [],
            "security_threats": [],
            "validation_issues": []
        }

        for filename, content in context.files:
            # 1. Tiedoston validointi
            file_issues = self.validate_file_content(filename, content)
            for issue in file_issues:
                report["validation_issues"].append(f"{filename}: {issue}")

            # 2. PII-skannaus
            pii = self.scan_for_pii(content)
            for item in pii:
                report["pii_findings"].append(f"{filename}: Löydetty {item['type']}")

            # 3. Injection-skannaus
            injections = self.detect_prompt_injection(content)
            for item in injections:
                report["security_threats"].append(f"{filename}: MAHDOLLINEN HYÖKKÄYS ({item['pattern']})")

        return report
