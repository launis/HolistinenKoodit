# Sovelluksen Julkaisu ja Jakaminen

Tässä ohjeessa käydään läpi kaksi tapaa jakaa tekemäsi Streamlit-sovellus:
1. **Hostaus pilvessä** (Suositeltu, helpoin tapa)
2. **Windows EXE-tiedoston luominen** (Vaativampi, hyvä jos tarvitaan täysin offline/paikallinen ratkaisu)

---

## Vaihtoehto A: Hostaus Pilvessä (Suositeltu)

Koska sovelluksesi on web-pohjainen (Streamlit), helpoin tapa jakaa se on laittaa se nettiin. Tällöin kuka tahansa voi käyttää sitä selaimella ilman asennuksia.

### 1. Streamlit Community Cloud (Helpoin)
Tämä on Streamlitin oma ilmainen palvelu.

1.  Varmista, että koodisi on **GitHubissa**.
2.  Mene osoitteeseen [share.streamlit.io](https://share.streamlit.io/).
3.  Kirjaudu sisään GitHub-tunnuksillasi.
4.  Paina "New app".
5.  Valitse GitHub-repositoriosi, haara (esim. `main`) ja pääohjelman tiedosto (`src/app.py`).
6.  Paina "Deploy".

**Huomioitavaa:**
*   Muista lisätä `requirements.txt` repositorioon (se sinulla jo onkin).
*   API-avaimet (`GOOGLE_API_KEY`) kannattaa asettaa Streamlit Cloudin asetuksissa ("Secrets"-kohdassa), ei koodissa.

### 2. Hugging Face Spaces
Toinen suosittu ja ilmainen vaihtoehto.

1.  Luo tili [Hugging Faceen](https://huggingface.co/).
2.  Luo uusi "Space".
3.  Valitse SDK:ksi **Streamlit**.
4.  Lataa tiedostosi sinne (voit käyttää git:iä tai web-käyttöliittymää).
5.  Aseta API-avaimet "Settings" -> "Variables and secrets" -kohdassa.

---

## Vaihtoehto B: Windows EXE-tiedoston luominen

Jos haluat ehdottomasti yhden tiedoston (`.exe`), jota voi ajaa ilman Python-asennusta, voit käyttää `PyInstaller`-työkalua. Streamlitin paketoiminen on hieman monimutkaisempaa kuin tavallisen skriptin, mutta tässä on ohjeet.

### 1. Asenna PyInstaller
Avaa terminaali ja suorita:
```bash
pip install pyinstaller
```

### 2. Luo käynnistystiedosto (`run_app.py`)
Luo projektisi juureen (sama kansio missä `src`-kansio on) uusi tiedosto nimeltä `run_app.py` ja kopioi sinne tämä koodi:

```python
import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    if getattr(sys, "frozen", False):
        basedir = sys._MEIPASS
    else:
        basedir = os.path.dirname(__file__)
    return os.path.join(basedir, path)

if __name__ == "__main__":
    # Määritä sovelluksen polku
    # Huom: Tässä oletetaan että src/app.py on paketoitu mukaan
    app_path = resolve_path(os.path.join("src", "app.py"))
    
    # Aseta argumentit ikään kuin komentoriviltä
    sys.argv = [
        "streamlit",
        "run",
        app_path,
        "--global.developmentMode=false",
    ]
    
    sys.exit(stcli.main())
```

### 3. Luo EXE-tiedosto komennolla
Suorita seuraava komento terminaalissa projektin juuressa. Tämä kertoo PyInstallerille, mitä tiedostoja otetaan mukaan.

```powershell
pyinstaller --noconfirm --onefile --windowed --name "HolistinenAgentti" `
 --hidden-import=streamlit `
 --collect-all streamlit `
 --collect-all google.generativeai `
 --add-data "src/app.py;src" `
 --add-data "src/agents.json;src" `
 --add-data "src/processor.py;src" `
 --copy-metadata streamlit `
 --copy-metadata google-generativeai `
 run_app.py
```

**Komennon selitys:**
*   `--onefile`: Pakkaa kaiken yhdeksi .exe-tiedostoksi.
*   `--windowed`: Piilottaa mustan komentorivi-ikkunan (jos haluat nähdä virheet, jätä tämä pois).
*   `--collect-all streamlit`: Ottaa mukaan kaikki Streamlitin tarvitsemat riippuvuudet.
*   `--add-data "src/...;src"`: Kopioi lähdekoodit exe:n sisään.

### 4. Lopputulos
Kun komento on valmis (voi kestää hetken), löydät `dist`-kansiosta tiedoston `HolistinenAgentti.exe`.

**Tärkeää EXE-tiedoston käytöstä:**
1.  **Käynnistys:** Kun käynnistät exe:n, se avaa selaimen ja lataa sovelluksen. Ensimmäinen käynnistys voi olla hidas, koska se purkaa tiedostoja väliaikaishakemistoon.
2.  **Ulkoiset tiedostot:** Sovelluksesi käyttää tiedostoa `Pääarviointikehote.docx`. Varmista, että tämä tiedosto on **samassa kansiossa** kuin `HolistinenAgentti.exe`, jotta ohjelma löytää sen.
3.  **.env tiedosto:** Jos käytät `.env`-tiedostoa API-avaimille, senkin pitää olla samassa kansiossa exe:n kanssa, tai sinun pitää syöttää API-avain käyttöliittymässä.

---

## Yhteenveto
*   Jos haluat vain jakaa sovelluksen kaverille tai kollegalle: **Käytä Streamlit Cloudia**.
*   Jos tarvitset täysin itsenäisen ohjelman USB-tikulle: **Tee EXE**.
