"""
Jakaa Pääarviointikehote.docx osiin:
- Yleiset_säännöt.txt (OSA 1-3 + Schema-määrittelyt)
- VAIHE_1.txt, VAIHE_2.txt, ... VAIHE_9.txt

Käynnistetään automaattisesti kun sovellus käynnistyy.
"""

from docx import Document
import re
import os

class PromptSplitter:
    def __init__(self, source_file="Pääarviointikehote.docx", output_dir="prompts"):
        self.source_file = source_file
        self.output_dir = output_dir
        
    def split_document(self):
        """Jakaa dokumentin osiin ja tallentaa ne."""
        print(f"Luetaan dokumenttia: {self.source_file}")
        
        # Lue dokumentti
        doc = Document(self.source_file)
        full_text = '\n'.join([p.text for p in doc.paragraphs])
        
        # Luo output-kansio jos ei ole
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 1. Erota yleiset säännöt (alusta VAIHE 1:een asti)
        common_rules = self._extract_common_rules(full_text)
        self._save_file("Yleiset_säännöt.txt", common_rules)
        print(f"✓ Tallennettu: Yleiset_säännöt.txt ({len(common_rules)} merkkiä)")
        
        # 2. Erota jokainen vaihe
        for i in range(1, 10):  # VAIHE 1-9
            phase_text = self._extract_phase(full_text, i)
            if phase_text:
                filename = f"VAIHE_{i}.txt"
                self._save_file(filename, phase_text)
                print(f"✓ Tallennettu: {filename} ({len(phase_text)} merkkiä)")
            else:
                print(f"⚠ VAIHE {i} ei löytynyt")
        
        print(f"\n✅ Dokumentti jaettu onnistuneesti! Tiedostot: {self.output_dir}/")
        return True
    
    def _extract_common_rules(self, text):
        """
        Erottaa yleiset säännöt.
        Yleiset säännöt = OSA 1-5 (ennen "OSA 6: AGENTTIEN TYÖNKULKU")
        """
        # Etsi "OSA 6: AGENTTIEN TYÖNKULKU"
        osa6_match = re.search(r'OSA 6[:\s]+AGENTTIEN TYÖNKULKU', text, re.IGNORECASE)
        if osa6_match:
            return text[:osa6_match.start()].strip()
        
        # Varasuunnitelma: Etsi ensimmäinen VAIHE
        vaihe_match = re.search(r'VAIHE 1[:\s]', text, re.IGNORECASE)
        if vaihe_match:
            return text[:vaihe_match.start()].strip()
        
        # Jos ei löydy, palauta ensimmäinen 30%
        return text[:len(text)//3]
    
    def _extract_phase(self, text, phase_num):
        """
        Erottaa tietyn vaiheen tekstin OSA 6:n sisältä.
        VAIHE-ohjeet ovat muodossa: "VAIHE X: Nimi"
        """
        # Etsi nykyinen vaihe
        current_patterns = [
            rf'VAIHE {phase_num}:',  # "VAIHE 1:"
            rf'VAIHE {phase_num}\s',  # "VAIHE 1 "
        ]
        
        current_match = None
        for pattern in current_patterns:
            current_match = re.search(pattern, text, re.IGNORECASE)
            if current_match:
                break
        
        if not current_match:
            return None
        
        start = current_match.start()
        
        # Etsi loppu
        # 1. Seuraava VAIHE
        # 2. OSA 7 (jos VAIHE 9)
        # 3. Dokumentin loppu
        
        end = len(text)
        
        if phase_num < 9:
            # Etsi seuraava VAIHE
            next_patterns = [
                rf'VAIHE {phase_num + 1}:',
                rf'VAIHE {phase_num + 1}\s',
            ]
            for pattern in next_patterns:
                next_match = re.search(pattern, text[start+10:], re.IGNORECASE)
                if next_match:
                    end = start + 10 + next_match.start()
                    break
        else:
            # VAIHE 9 - etsi OSA 7
            osa7_match = re.search(r'OSA 7[:\s]', text[start+10:], re.IGNORECASE)
            if osa7_match:
                end = start + 10 + osa7_match.start()
        
        phase_text = text[start:end].strip()
        
        # Poista OSA 4-7 sisältö jos se on mukana
        # (Tämä voi tapahtua jos VAIHE 9:n jälkeen tulee OSA 4-7)
        osa_match = re.search(r'OSA [4-7][:\s]', phase_text[100:], re.IGNORECASE)
        if osa_match:
            phase_text = phase_text[:100 + osa_match.start()].strip()
        
        return phase_text
    
    def _save_file(self, filename, content):
        """Tallentaa tiedoston output-kansioon."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
    
    def get_prompt_modules(self):
        """
        Lukee jaetut tiedostot ja palauttaa ne sanakirjana.
        Käytetään context.py:ssä.
        """
        modules = {}
        
        # Lue yleiset säännöt
        common_path = os.path.join(self.output_dir, "Yleiset_säännöt.txt")
        if os.path.exists(common_path):
            with open(common_path, 'r', encoding='utf-8') as f:
                modules['COMMON_RULES'] = f.read()
        
        # Lue vaiheet
        for i in range(1, 10):
            phase_path = os.path.join(self.output_dir, f"VAIHE_{i}.txt")
            if os.path.exists(phase_path):
                with open(phase_path, 'r', encoding='utf-8') as f:
                    modules[f'VAIHE {i}'] = f.read()
        
        return modules


def split_prompt_on_startup(source_file="Pääarviointikehote.docx"):
    """
    Kutsutaan sovelluksen käynnistyessä.
    Jakaa Pääarviointikehote.docx osiin jos se on olemassa.
    """
    if not os.path.exists(source_file):
        print(f"⚠ Tiedostoa {source_file} ei löydy. Ohitetaan jako.")
        return None
    
    splitter = PromptSplitter(source_file)
    splitter.split_document()
    return splitter


if __name__ == "__main__":
    # Testaus: Aja tämä suoraan
    split_prompt_on_startup()
