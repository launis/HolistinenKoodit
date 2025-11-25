"""
Jakaa Pääarviointikehote.docx osiin:
- Yleiset_säännöt.txt (OSA 1-3 + Schema-määrittelyt)
- VAIHE_1.txt, VAIHE_2.txt, ... VAIHE_9.txt

Käynnistetään automaattisesti kun sovellus käynnistyy.
"""

from docx import Document
import re
import os

import json
import json
try:
    from config import PHASES
except ImportError:
    from src.config import PHASES

class PromptSplitter:
    def __init__(self, source_file="Pääarviointikehote.docx"):
        self.source_file = source_file
        self.modules = {} # Store modules in memory: {'COMMON_RULES': '...', 'VAIHE 1': '...'}
        
    def split_document(self):
        """Jakaa dokumentin osiin ja tallentaa ne muistiin."""
        # print(f"Luetaan dokumenttia: {self.source_file}")
        
        try:
            # Lue dokumentti
            doc = Document(self.source_file)
            # FIX: Use '\n' (newline) instead of '\\n' (literal backslash n)
            full_text = '\n'.join([p.text for p in doc.paragraphs])
            
            # 1. Erota yleiset säännöt (alusta VAIHE 1:een asti)
            common_rules = self._extract_common_rules(full_text)
            self.modules['COMMON_RULES'] = common_rules
            # print(f"✓ Parsittu: Yleiset säännöt ({len(common_rules)} merkkiä)")
            
            # 2. Erota jokainen vaihe
            for i in range(1, 10):  # VAIHE 1-9
                phase_text = self._extract_phase(full_text, i)
                if phase_text:
                    # Jälkikäsittely: Lisää placeholderit ja skeemaesimerkit
                    phase_text = self._post_process_phase(i, phase_text)
                    self.modules[f'VAIHE {i}'] = phase_text
                    # print(f"✓ Parsittu: VAIHE {i} ({len(phase_text)} merkkiä)")
                # else:
                    # print(f"⚠ VAIHE {i} ei löytynyt")
            
            return True
        except Exception as e:
            print(f"Virhe dokumentin jakamisessa: {e}")
            return False

    def _post_process_phase(self, phase_number, text):
        """
        Lisää tekniset ohjeet (placeholderit ja JSON-esimerkit) promptiin.
        Tämä varmistaa, että ne ovat mukana vaikka DOCX ylikirjoitettaisiin.
        """
        
        # 1. VAIHE 1: Placeholder-injektio (MAX_TOKENS esto)
        if phase_number == 1:
            replacements = {
                "keskusteluhistoria: string;   // Puhdistettu raakateksti": 'keskusteluhistoria: string;   // ÄLÄ TULOSTA SISÄLTÖÄ! Käytä VAIN tätä tekstiä: "{{FILE: Keskusteluhistoria.pdf}}"',
                "lopputuote: string;           // Puhdistettu raakateksti": 'lopputuote: string;           // ÄLÄ TULOSTA SISÄLTÖÄ! Käytä VAIN tätä tekstiä: "{{FILE: Lopputuote.pdf}}"',
                "reflektiodokumentti: string;  // Puhdistettu raakateksti": 'reflektiodokumentti: string;  // ÄLÄ TULOSTA SISÄLTÖÄ! Käytä VAIN tätä tekstiä: "{{FILE: Reflektiodokumentti.pdf}}"'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)

        # 2. KAIKKI VAIHEET (paitsi 9): Skeemaesimerkin injektio
        if phase_number < 9:
            # Etsi oikea vaihe konfiguraatiosta
            phase_config = next((p for p in PHASES if p["id"] == f"phase_{phase_number}"), None)
            
            if phase_config and "schema" in phase_config:
                # Generoi esimerkki skeemasta (Config.py on primääri lähde)
                example_obj = self._generate_example_from_schema(phase_config["schema"])
                example_json = json.dumps(example_obj, indent=2, ensure_ascii=False)
                
                injection = f"""
KÄSKE: (Esimerkki oikeasta rakenteesta):
Sinun TÄYTYY noudattaa tätä rakennetta (huomaa tarkat avaimet!):
{example_json}
ÄLÄ käytä avaimia kuten "pisteytys", "taso" tai "kriteeri1" ellei niitä ole yllä mainittu. Käytä vain yllä olevia.
"""
                # Lisää loppuun ennen "Älä tulosta mitään muuta..." jos mahdollista, tai vain loppuun
                if "Älä tulosta mitään muuta tämän jälkeen." in text:
                    text = text.replace("Älä tulosta mitään muuta tämän jälkeen.", injection + "\nÄlä tulosta mitään muuta tämän jälkeen.")
                else:
                    text += injection

        return text

    def _generate_example_from_schema(self, schema):
        """Generoi esimerkkiobjektin rekursiivisesti skeeman perusteella."""
        if schema.get("type") == "object":
            obj = {}
            for prop_name, prop_schema in schema.get("properties", {}).items():
                obj[prop_name] = self._generate_example_from_schema(prop_schema)
            return obj
        
        elif schema.get("type") == "array":
            # Luodaan lista, jossa on yksi esimerkki-item
            item_schema = schema.get("items", {})
            return [self._generate_example_from_schema(item_schema)]
            
        elif "example" in schema:
            return schema["example"]
            
        else:
            # Fallback oletusarvot jos example puuttuu
            t = schema.get("type")
            if t == "string": return "..."
            if t == "boolean": return False
            if t == "number": return 0
            if t == "integer": return 0
            return None

    def _extract_common_rules(self, text):
        """
        Erottaa tekstin alusta ensimmäiseen 'VAIHE 1:' -merkintään asti.
        Käyttää pituusrajoitusta (max 100 merkkiä) ja varmistaa, ettei rivi lopu tavuviivaan (-)
        joka viittaisi katkenneeseen sanaan/lauseeseen.
        """
        pattern = r"(?m)^VAIHE 1:.{0,100}(?<!-)$"
        match = re.search(pattern, text)
        if match:
            return text[:match.start()].strip()
        return ""

    def _extract_phase(self, text, phase_number):
        """
        Erottaa tietyn vaiheen tekstin.
        Käyttää pituusrajoitusta ja tavuviivan tarkistusta otsikoiden tunnistamiseen.
        """
        start_marker = f"VAIHE {phase_number}:"
        end_marker = f"VAIHE {phase_number + 1}:"
        
        # Etsi alkukohta (rivin alusta, max 100 merkkiä, ei lopu tavuviivaan)
        start_pattern = f"(?m)^{start_marker}.{{0,100}}(?<!-)$"
        start_match = re.search(start_pattern, text)
        
        if not start_match:
            return ""
            
        start_index = start_match.start()
        
        if phase_number == 9:
            # Viimeinen vaihe, otetaan loppuun asti
            return text[start_index:].strip()
        else:
            # Etsi loppukohta (seuraava vaihe rivin alusta, max 100 merkkiä, ei lopu tavuviivaan)
            end_pattern = f"(?m)^{end_marker}.{{0,100}}(?<!-)$"
            end_match = re.search(end_pattern, text)
            
            if end_match:
                return text[start_index:end_match.start()].strip()
            
            # Fallback: jos seuraavaa vaihetta ei löydy
            return text[start_index:].strip()
    
    def get_prompt_modules(self):
        """
        Palauttaa jaetut moduulit sanakirjana.
        """
        return self.modules

    def save_to_disk(self, output_dir="prompts"):
        """Tallentaa moduulit tekstitiedostoiksi."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Tallenna yleiset säännöt
        if 'COMMON_RULES' in self.modules:
            with open(os.path.join(output_dir, "Yleiset_säännöt.txt"), "w", encoding="utf-8") as f:
                f.write(self.modules['COMMON_RULES'])
                
        # Tallenna vaiheet
        for key, content in self.modules.items():
            if key.startswith("VAIHE"):
                filename = f"{key.replace(' ', '_')}.txt"
                with open(os.path.join(output_dir, filename), "w", encoding="utf-8") as f:
                    f.write(content)
        
        # print(f"✓ Tallennettu {len(self.modules)} tiedostoa kansioon {output_dir}")


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
    splitter.save_to_disk()
    return splitter


if __name__ == "__main__":
    # Testaus: Aja tämä suoraan
    split_prompt_on_startup()
