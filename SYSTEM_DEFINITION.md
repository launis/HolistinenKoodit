# Järjestelmän Määrittely ja Arkkitehtuuri (System Definition)

Tämä dokumentti kuvaa **Holistinen Mestaruus 3.0** -järjestelmän arkkitehtuurin, komponentit ja testauksen tilan.

## 1. Johdanto

Järjestelmä on tekoälyavusteinen arviointityökalu, joka analysoi opiskelijoiden palauttamia dokumentteja (Keskusteluhistoria, Lopputuote, Reflektio) ja tuottaa niistä kattavan arviointiraportin PDF-muodossa. Prosessi on jaettu 9 vaiheeseen, joita ohjaa orkestrointikerros.

## 2. Järjestelmäarkkitehtuuri

Järjestelmä noudattaa kerrosarkkitehtuuria (Layered Architecture), jossa käyttöliittymä, orkestrointi, datankäsittely ja tekoälypalvelut on eriytetty.

### 2.1 Komponenttikaavio

```mermaid
graph TD
    User((Käyttäjä))
    UI[Streamlit UI (app.py)]
    Orchestrator[Orchestrator (orchestrator.py)]
    LLM[LLM Service (llm_service.py)]
    Data[Data Handler (data_handler.py)]
    Report[Report Generator (report_generator.py)]
    Security[Security Validator (security_validator.py)]
    Search[Search Service (search_service.py)]
    
    User -->|Lataa tiedostot & Konfiguroi| UI
    UI -->|Käynnistä prosessi| Orchestrator
    Orchestrator -->|Lue tiedostot| Data
    Orchestrator -->|Validoi syöte| Security
    Orchestrator -->|Suorita vaiheet| LLM
    Orchestrator -->|Tarkista faktat| Search
    Orchestrator -->|Generoi raportti| Report
    Report -->|Tallenna PDF| UI
    UI -->|Lataa PDF| User
```

### 2.2 Tietovirta (Data Flow)

Prosessi etenee seuraavasti:

1.  **Syöte**: Käyttäjä lataa PDF/TXT-tiedostot.
2.  **Esikäsittely**: `DataHandler` lukee ja puhdistaa tekstin (PyMuPDF).
3.  **Turvallisuustarkistus**: `SecurityValidator` tarkistaa syötteet (PII, haitallinen koodi).
4.  **Orkestrointi (Vaiheet 1-8)**:
    *   `Orchestrator` rakentaa kehotteet (Prompts) `AssessmentContext`:in avulla.
    *   `LLMService` kutsuu Gemini-mallia.
    *   Tulokset tallennetaan kontekstiin ja JSON-muotoon.
5.  **Faktantarkistus (Vaihe 7)**: `SearchService` tarkistaa kriittiset väitteet Google Search API:lla.
6.  **Raportointi (Vaihe 9)**: `ReportGenerator` kokoaa JSON-tulokset ja luo lopullisen PDF-raportin.

## 3. Komponentit

| Komponentti | Kuvaus |
| :--- | :--- |
| **app.py** | Streamlit-pohjainen käyttöliittymä. Hallinnoi session tilaa ja käyttäjäinteraktiota. |
| **orchestrator.py** | Sovelluslogiikan ydin. Ohjaa prosessin kulkua vaiheesta toiseen ja käsittelee virhetilanteet. |
| **llm_service.py** | Rajapinta Google Gemini -malleihin. Hoitaa API-kutsut ja virheenkäsittelyn (retry logic). |
| **data_handler.py** | Vastaa tiedostojen lukemisesta ja tekstin erottelusta (PDF/TXT). |
| **report_generator.py** | Muuntaa analyysitulokset (JSON/Markdown) muotoilluksi PDF-raportiksi. |
| **security_validator.py** | Suorittaa syötteiden validoinnin ja sanitioinnin ennen LLM-käsittelyä. |
| **prompt_splitter.py** | Pilkkoo suuren `Pääarviointikehote.docx` -tiedoston hallittaviksi osiksi. |

## 4. Testauksen Tila

Järjestelmän toiminnallisuus on varmistettu kattavilla yksikkö- ja integraatiotesteillä.

### 4.1 Suoritetut Testit

*   **Järjestelmäintegraatio (`test_system_flow.py`)**: ✅
    *   Testaa koko putken alusta loppuun (E2E).
    *   Varmistaa, että kaikki komponentit toimivat yhdessä.
*   **PDF-käsittely (`test_pdf_handler.py`)**: ✅
    *   Varmistaa tekstin erottelun tarkkuuden (PyMuPDF).
*   **JSON-korjaus (`test_json_cleaner.py`)**: ✅
    *   Testaa LLM:n tuottaman viallisen JSON:in automaattista korjausta.
*   **Raportin generointi (`test_both_formats.py`)**: ✅
    *   Varmistaa, että PDF-raportti syntyy oikein sekä uudella että vanhalla JSON-rakenteella.
*   **Turvallisuus (`test_security_validator.py`)**: ✅
    *   Testaa PII-tietojen ja haitallisen sisällön tunnistusta.

### 4.2 Yhteenveto

Järjestelmä on **tuotantovalmis**. Kriittiset polut (tiedostojen luku, LLM-integraatio, raportointi) on testattu ja todettu toimiviksi. Tunnetut ongelmat (kuten satunnaiset JSON-muotoiluvirheet) on taklattu automaattisella korjauslogiikalla.
