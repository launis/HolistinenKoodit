import json
import re
import ast

class ReportGenerator:
    # ... (alku pysyy samana)

    def _extract_json(self, text):
        """Etsii ja parsii JSON-lohkon tekstistä."""
        # 1. Yritä etsiä markdown-koodilohkoa
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)

        # 2. Etsi kaikki mahdolliset JSON-objektit ({...})
        candidates = []
        stack = []
        start_index = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start_index = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        candidates.append(text[start_index:i+1])
        
        if not candidates:
            # Fallback: koko teksti
            candidates = [text]

        # 3. Yritä parsia kandidaatit
        for json_str in reversed(candidates):
            # A. Standardi JSON
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
            
            # B. Python-syntaksi (ast.literal_eval) - hoitaa yksinkertaiset lainausmerkit ('key': 'val')
            try:
                return ast.literal_eval(json_str)
            except (ValueError, SyntaxError):
                pass

            # C. Regex-korjaus (viimeinen oljenkorsi)
            try:
                fixed = self._repair_json(json_str)
                return json.loads(fixed)
            except:
                continue
        
        return None

    def generate_report(self, context):
        """
        Luo raportin markdown-muodossa käyttäen Holistinen Mestaruus 3.0 -rakennetta.
        """
        # 1. Hae Vaiheen 8 tulos kontekstista
        phase_8_result = context.results.get("phase_8")
        if not phase_8_result:
            phase_8_result = context.results.get("VAIHE 8")
        
        if not phase_8_result:
            return "VIRHE: Vaiheen 8 tuloksia ei löytynyt. Raporttia ei voida luoda."

        # 2. Parsi JSON (käytetään robustia _extract_json-metodia)
        data = self._extract_json(phase_8_result)
        if not data:
            return f"VIRHE: Vaiheen 8 tulos ei ollut validia JSON-muotoa.\n\nAlkuperäinen tulos:\n{phase_8_result}"

        # 3. Rakenna raportti (Käyttäjän mallin mukaisesti)
        tuomio = data.get('tuomio', {})
        # Jos 'tuomio' puuttuu, yritetään etsiä sitä tai käyttää dataa suoraan
        if not tuomio and 'pisteet' in data:
            tuomio = data
        
        meta = data.get('metadata', {})
        
        report = []
        
        # 0. ALKUTULOSTUS
        report.append(f"=== TIEDOSTO: 8_tuomio_ja_pisteet.json ===")
        report.append("```json")
        report.append(json.dumps(data, indent=2, ensure_ascii=False))
        report.append("```")
        report.append("\n" + "="*50 + "\n")

        # --- OSA 1: YHTEENVETO JA KRIITTISET HAVAINNOT ---
        report.append("OSA 1: YHTEENVETO JA KRIITTISET HAVAINNOT")
        
        # Päätelmät
        summary_text = data.get('semanttinen_tarkistussumma', '')
        resolution = tuomio.get('konfliktinratkaisu', '')
        if not resolution:
             resolution = self._find_value(data, ['ratkaisun_peruste', 'konfliktinratkaisu'])
        
        report.append(f"\nPäätelmät:\n{summary_text}\nRatkaisumalli: {resolution}")
        
        # Kriittiset Havainnot
        observations = tuomio.get('kriittiset_havainnot', [])
        if not observations:
             observations = self._find_value(data, ['kriittiset_havainnot', 'critical_findings'])
             
        report.append("\nKriittiset Havainnot:")
        if observations:
            if isinstance(observations, list):
                for obs in observations:
                    if isinstance(obs, dict):
                        report.append(f"- {obs.get('tyyppi', 'Havainto')}: {obs.get('kuvaus', '')}")
                    else:
                        report.append(f"- {obs}")
            else:
                report.append(f"- {observations}")
        else:
            report.append("- Ei kriittisiä havaintoja.")

        # HITL-VAHVISTUS
        report.append("\nHITL-VAHVISTUS VAADITAAN:")
        report.append("”Järjestelmä ei voinut varmentaa heterogeenista ajoa (eri perusmallit eri agenteille). VAROITUS: Jos ajo on suoritettu homogeenisesti, Kriitikkoryhmän ristiinvalidoinnin hyöty on mitätöity ja systeemisen hallusinaation riski on KORKEA (Ye ym. 2025). Arvioinnin luotettavuusaste (Reliability Score) laskee automaattisesti tasolle EHDOLLEINEN. Vahvistatko manuaalisesti, että ajo oli heterogeeninen ja agenttien eristys on toiminut?”")
        
        # Eettiset huomiot
        ethics = tuomio.get('eettiset_ja_periaatteelliset_huomiot', [])
        if not ethics:
             ethics = self._find_value(data, ['eettiset_ja_periaatteelliset_huomiot', 'eettiset_huomiot'])

        report.append("\nEettiset ja Periaatteelliset Huomiot (SÄÄNTÖ 9):")
        if ethics:
            if isinstance(ethics, list):
                for eth in ethics:
                    report.append(f"HUOMIO: {eth}")
            elif isinstance(ethics, dict):
                 desc = ethics.get('kuvaus')
                 if desc: report.append(f"HUOMIO: {desc}")
                 else: report.append(f"HUOMIO: {ethics}")
            else:
                report.append(f"HUOMIO: {ethics}")
        else:
            report.append("Ei merkittäviä eettisiä tai periaatteellisia huomioita.")

        # --- OSA 2: ANALYYTTINEN ARVIOINTI ---
        report.append("\nOSA 2: ANALYYTTINEN ARVIOINTI")
        report.append("") # Tyhjä rivi otsikon jälkeen
        
        # Yritä etsiä arviointidataa eri avaimilla
        scores = tuomio.get('pisteet', {})
        if not scores:
             scores = tuomio.get('pisteytys', {})
        if not scores:
             scores = self._find_value(data, ['pisteet', 'pisteytys', 'arviointi']) or {}
        
        # Apufunktio tietojen hakuun
        def get_criteria_data(keys):
            val = self._find_value(scores, keys)
            if isinstance(val, dict):
                # Hae pisteet: 'arvosana', 'pisteet' tai 'taso'
                score = val.get('arvosana')
                if score is None: score = val.get('pisteet')
                if score is None: score = val.get('taso', 'N/A')
                
                # Hae perustelu: 'perustelu' tai 'kuvaus'
                reason = val.get('perustelu')
                if not reason: reason = val.get('kuvaus', '[Perustelu puuttuu]')
                
                return score, reason
            return val if val is not None else 'N/A', '[Perustelu puuttuu]'

        # Kriteeri 1: Analyysi ja Prosessin Tehokkuus
        report.append("Kriteeri 1: Analyysi ja Prosessin Tehokkuus")
        s1, p1 = get_criteria_data(['analyysi_ja_prosessi', 'kriteeri1_analyysi', 'kriteeri_1_analyysi', 'analyysi'])
        report.append(f"\nPistemäärä: {s1}/4")
        report.append(f"\nPerustelu: {p1}")

        # Kriteeri 2: Arviointi ja Argumentaatio
        report.append("\n\nKriteeri 2: Arviointi ja Argumentaatio")
        s2, p2 = get_criteria_data(['arviointi_ja_argumentaatio', 'kriteeri2_reflektio', 'kriteeri_2_reflektio', 'kriteeri_2_prosessi_ohjaus', 'kriteeri_2_vuorovaikutus', 'vuorovaikutus'])
        report.append(f"\nPistemäärä: {s2}/4")
        report.append(f"\nPerustelu: {p2}")

        # Kriteeri 3: Synteesi ja Luovuus
        report.append("\n\nKriteeri 3: Synteesi ja Luovuus")
        s3, p3 = get_criteria_data(['synteesi_ja_luovuus', 'kriteeri3_synteesi', 'kriteeri_3_synteesi', 'synteesi'])
        report.append(f"\nPistemäärä: {s3}/4")
        
        # Erityisperustelu jos Mestaruus-poikkeama
        mp = tuomio.get('masteruus_poikkeama') or self._find_value(data, ['masteruus_poikkeama', 'mestaruus_poikkeama'])
        if mp:
            mp_reason = tuomio.get('masteruus_poikkeama_perustelu') or self._find_value(data, ['masteruus_poikkeama_perustelu', 'perustelu'])
            # Jos mp_reason on sama kuin p3, ei tulosteta uudestaan
            if mp_reason and mp_reason != p3:
                 report.append(f"\nPerustelu (Mestaruus-poikkeama): {mp_reason}")
            else:
                 report.append(f"\nPerustelu: {p3}")
        else:
            report.append(f"\nPerustelu: {p3}")

        # --- OSA 3: XAI-RAPORTTI ---
        report.append("\nOSA 3: XAI-RAPORTTI (LÄPINÄKYVYYS JA EPÄVARMUUS)")
        
        # 3.1 Kriittiset Auditointikysymykset
        report.append("\n3.1. KRIITTISET AUDITOINTIKYSYMYKSET (HITL-VASTAUS VAADITAAN)")
        
        aitous_epaily = False
        if observations and isinstance(observations, list):
            for obs in observations:
                obs_str = str(obs)
                if "AITOUS-EPÄILY" in obs_str or "Epäilyttävän Täydellinen" in obs_str:
                    aitous_epaily = True
                    report.append(f"- KYSELY: Järjestelmä liputti suorituksen 'Epäilyttävän Täydelliseksi'. Vahvistatko ihmisvarmistajana, että prosessi vaikuttaa orgaaniselta eikä performatiiviselta?")
        
        if not aitous_epaily:
            report.append("[Ei automaattisesti generoituja kysymyksiä]")

        # 3.2 Epävarmuuden kartoitus
        report.append("\n3.2. EPÄVARMUUDEN KARTOITUS")
        
        report.append("Aleatorinen Epävarmuus (Datan Luonne):")
        report.append("- Datan epätäydellisyys tai ristiriitaisuus (analysoidaan syötedatasta).")

        report.append("\nSysteeminen Epävarmuus (Arkkitehtuurin ja Prosessin Rajoitteet):")
        report.append(f"- Metodologinen loki: {data.get('metodologinen_loki', 'Ei lokimerkintöjä')}")
        
        report.append("\nProsessirajoitteet ja Turvallisuus:")
        report.append("Kognitiivisen Palomuurin Hauraus (SÄÄNTÖ 1): \"KORKEA EPÄVARMUUS: Järjestelmän hallinta perustuu kehotepohjaiseen (behavioraaliseen) kontrolliin. Tämä menetelmä on luontaisesti hauras ja altis manipuloinnille (Liu, Y. ym. 2023).\"")
        
        report.append("\nEpisteeminen Epävarmuus (Päättelyn Rajallisuus):")
        epistemic = tuomio.get('episteeminen_epavarmuus', [])
        if not epistemic:
             epistemic = self._find_value(data, ['episteeminen_epavarmuus'])
             
        if epistemic:
            if isinstance(epistemic, list):
                for ep in epistemic:
                    report.append(f"- {ep}")
            else:
                report.append(f"- {epistemic}")
        else:
            report.append("- Ei tunnistettuja episteemisiä rajoitteita.")

        # --- OSA 4: VASTUUVAPAUSLAUSEKE ---
        report.append("\nOSA 4: VASTUUVAPAUSLAUSEKE JA KÄYTTÖRAJOITUKSET")
        report.append("”Tämä raportti on tuotettu automatisoidun moniagenttijärjestelmän (\"Kognitiivinen Kvoorum\") toimesta. Se on tarkoitettu päätöksenteon tueksi, ei sen korvaajaksi. EU:n tekoälyasetuksen ja eettisten ohjeistusten (Euroopan komission korkean tason asiantuntijaryhmä 2019) mukaisesti tätä arviota ei tule käyttää ainoana perusteena korkean panoksen (high-stakes) päätöksille ilman pätevän ihmisasiantuntijan suorittamaa varmistusta (Human-in-the-Loop).”")

        return "\n".join(report)

    def _extract_json(self, text):
        """Etsii ja parsii JSON-lohkon tekstistä."""
        # 1. Yritä etsiä markdown-koodilohkoa
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
        if match:
            text = match.group(1)

        # 2. Etsi kaikki mahdolliset JSON-objektit ({...})
        # Käytetään pinoa (stack) löytämään tasapainotetut aaltosulkeet
        candidates = []
        stack = []
        start_index = -1
        
        for i, char in enumerate(text):
            if char == '{':
                if not stack:
                    start_index = i
                stack.append(char)
            elif char == '}':
                if stack:
                    stack.pop()
                    if not stack:
                        # Löydettiin kokonainen blokki
                        candidates.append(text[start_index:i+1])
        
        # Jos ei löytynyt yhtään, palauta virhe
        if not candidates:
            return None

        # 3. Yritä parsia kandidaatit, aloita viimeisestä (usein lopullinen vastaus)
        for json_str in reversed(candidates):
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                # Yritä korjata
                try:
                    fixed = self._repair_json(json_str)
                    return json.loads(fixed)
                except:
                    continue
        
        return None

    def _repair_json(self, json_str):
        """Yrittää korjata yleisiä JSON-virheitä."""
        # Poista kommentit (// ...)
        json_str = re.sub(r"//.*", "", json_str)
        # Poista trailing commas
        json_str = re.sub(r",\s*([\]}])", r"\1", json_str)
        # Korvaa yksinkertaiset lainausmerkit kaksinkertaisilla (varovasti)
        # Tämä on riski jos tekstissä on heittomerkkejä, mutta välttämätön jos malli käyttää 'key': 'val'
        # Yritetään korvata vain jos ne näyttävät JSON-avaimilta tai arvoilta
        json_str = re.sub(r"\'\s*:\s*\'", '": "', json_str) # 'key': 'val' -> "key": "val"
        json_str = re.sub(r"\'\s*:\s*([0-9])", '": \1', json_str) # 'key': 123 -> "key": 123
        json_str = re.sub(r"([{\[,])\s*\'", r'\1"', json_str) # {'key' -> {"key"
        json_str = re.sub(r"\'\s*([}\],])", r'"\1', json_str) # 'val'} -> "val"}
        
        return json_str

    def _find_value(self, data, keys):
        """Etsii arvoa sanakirjasta (myös sisäkkäisistä) annetuilla avaimilla (case-insensitive)."""
        if not isinstance(data, dict):
            return None
        
        # Muunna hakuavaimet pieniksi kirjaimiksi
        keys_lower = [k.lower() for k in keys]
            
        # 1. Etsi suoraan (case-insensitive)
        for k, v in data.items():
            if k.lower() in keys_lower:
                return v
        
        # 2. Etsi sisäkkäisistä sanakirjoista (esim. "response": {...})
        for v in data.values():
            if isinstance(v, dict):
                found = self._find_value(v, keys)
                if found: return found
                
        return None
