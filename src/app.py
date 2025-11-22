import streamlit as st
import json
import os
import google.generativeai as genai
from dotenv import load_dotenv
from processor import AIProcessor

# Lataa ympäristömuuttujat .env-tiedostosta
load_dotenv()

# Sivun asetukset
st.set_page_config(page_title="Parviointikehote Agentit", layout="wide")

st.title("🤖 Parviointikehote - Agenttien Ajo")

# Sivupalkki asetuksille
with st.sidebar:
    st.header("Asetukset")
    
    # Hae API-avain ympäristömuuttujista tai näytä tyhjä kenttä
    default_api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key = st.text_input("Gemini API Key", value=default_api_key, type="password").strip()
    
    if not api_key:
        st.warning("Syötä API-avain joko tähän tai .env-tiedostoon.")

    # Alusta prosessori heti, jotta saadaan mallit
    processor = AIProcessor(api_key=api_key)
    
    # Hae mallit dynaamisesti, jos avain on olemassa
    if api_key:
        available_models = processor.get_available_models()
        # Suositaan tiettyjä malleja oletuksena
        default_index = 0
        if "gemini-flash-latest" in available_models:
            default_index = available_models.index("gemini-flash-latest")
        elif "gemini-1.5-flash" in available_models:
            default_index = available_models.index("gemini-1.5-flash")
        elif "gemini-pro" in available_models:
            default_index = available_models.index("gemini-pro")
            
        model_selection = st.selectbox("Valitse malli", available_models, index=default_index)
    else:
        model_selection = st.selectbox("Valitse malli", ["gemini-flash-latest", "gemini-1.5-flash", "gemini-pro"])
    
    st.subheader("Agentit")
    try:
        with open(os.path.join(os.path.dirname(__file__), 'agents.json'), 'r', encoding='utf-8') as f:
            agents = json.load(f)
        st.success(f"Ladattu {len(agents)} agenttia.")
    except FileNotFoundError:
        st.error("agents.json ei löytynyt!")
        agents = []

# Pääalue
# Pääalue
st.header("1. Lataa tiedostot")
col1, col2, col3 = st.columns(3)

with col1:
    historia_file = st.file_uploader("Keskusteluhistoria (PDF)", type=['pdf', 'txt'])
with col2:
    lopputuote_file = st.file_uploader("Lopputuote (PDF)", type=['pdf', 'txt'])
with col3:
    reflektio_file = st.file_uploader("Reflektiodokumentti (PDF)", type=['pdf', 'txt'])

uploaded_files = [f for f in [historia_file, lopputuote_file, reflektio_file] if f is not None]

# Lataa Pääarviointikehote (Mahdollisuus ladata uusi versio UI:sta)
st.subheader("Pääarviointikehote")
custom_prompt_file = st.file_uploader("Lataa uusi Pääarviointikehote (DOCX)", type=['docx'])

system_instructions = ""
if custom_prompt_file:
    try:
        system_instructions = processor._read_docx(custom_prompt_file)
        st.success("✅ Käytetään ladattua Pääarviointikehotetta.")
    except Exception as e:
        st.error(f"Virhe ladattaessa tiedostoa: {str(e)}")
else:
    # Fallback: Oletustiedosto
    try:
        prompt_path = os.path.join(os.getcwd(), "Pääarviointikehote.docx")
        if os.path.exists(prompt_path):
            system_instructions = processor._read_docx(prompt_path)
            st.info(f"ℹ️ Käytetään oletuskehotetta (löytyi kansiosta).")
        else:
            st.warning(f"⚠️ Pääarviointikehote.docx ei löytynyt kansiosta, eikä uutta ladattu.")
    except Exception as e:
        st.error(f"Virhe ladattaessa oletuskehotetta: {str(e)}")

# Määritellään orkestrointivaiheet
ORCHESTRATION_STEPS = [
    {
        "id": "moodi_a",
        "name": "Vaihe 1: Alustus (Vartija, Analyytikko, Loogikko)",
        "model_type": "model_a", 
        "task_prompt": """
        Noudata Ajo_Tiedosto.docx ohjeita (MOODI A).
        Suorita VAIHEET 1, 2 ja 3 peräkkäin.
        Tulosta vastauksena YKSI AINOA koodilohko, joka sisältää kaikki kolme JSON-tiedostoa 
        (1_tainted_data.json, 2_todistuskartta.json, 3_argumentaatioanalyysi.json) 
        eroteltuna === TIEDOSTO: ... === -tunnisteilla.
        """
    },
    {
        "id": "moodi_b",
        "name": "Vaihe 2: Auditointi (Kriitikkoryhmä)",
        "model_type": "model_b", 
        "task_prompt": """
        Noudata Ajo_Tiedosto.docx ohjeita (MOODI B).
        Toimit nyt Kriitikkoryhmänä. Lue syötedata (JSONit 1-3).
        Suorita rinnakkain VAIHEET 4, 5, 6 ja 7.
        Tulosta vastauksena YKSI AINOA koodilohko, joka sisältää uudet JSON-tiedostot 
        (4_logiikka_auditointi.json, 5_kausaalinen_auditointi.json, 
        6_performatiivisuus_auditointi.json, 7_falsifiointi_ja_etiikka.json).
        """
    },
    {
        "id": "moodi_c",
        "name": "Vaihe 3: Synteesi (Tuomari & XAI)",
        "model_type": "model_a", 
        "task_prompt": """
        Noudata Ajo_Tiedosto.docx ohjeita (MOODI C).
        Lue kaikki aiempi prosessidata (JSONit 1-7).
        Suorita VAIHE 8 (Tuomari) ja VAIHE 9 (XAI-Raportoija).
        Tulosta ensin 8_tuomio_ja_pisteet.json omana koodilohkonaan ja 
        sen jälkeen Lopullinen Arviointiraportti tekstimuodossa OSA 7 mukaisesti.
        """
    }
]

tab1, tab2 = st.tabs(["Orkestrointi", "Yksittäiset Agentit"])

with tab1:
    st.info("Orkestrointi suorittaa monivaiheisen prosessin käyttäen Pääarviointikehotetta.")
    if st.button("Käynnistä Orkestrointi", type="primary", disabled=not uploaded_files or not system_instructions):
        st.header("Orkestroinnin Tulokset")
        
        # Placeholderit tuloksille
        results_placeholders = {step['id']: st.empty() for step in ORCHESTRATION_STEPS}
        
        results = {}
        current_context = f"{system_instructions}\n\n"
        # Lisätään tiedostot kontekstiin
        for uploaded_file in uploaded_files:
             current_context += f"\n--- TIEDOSTO: {uploaded_file.name} ---\n{processor._read_file_content(uploaded_file)}\n"

        model_a_name = model_selection # Käytetään valittua mallia A:na
        model_b_name = model_selection # Käytetään valittua mallia B:na
        
        for step in ORCHESTRATION_STEPS:
            step_id = step["id"]
            with results_placeholders[step_id].container():
                
                # Valitse malli
                if step["model_type"] == "model_a":
                    selected_model = model_a_name
                else:
                    # Tarkista onko model_b saatavilla, muuten käytä model_a
                    if model_b_name in processor.get_available_models():
                        selected_model = model_b_name
                    else:
                        selected_model = model_a_name
                
                # Rakenna prompt
                context_with_history = current_context
                if results:
                    context_with_history += "\n\n--- AIEMMAT TULOKSET ---\n"
                    for key, val in results.items():
                        context_with_history += f"\n=== VAIHE: {key} ===\n{val}\n"
                
                final_prompt = f"{context_with_history}\n\n--- TEHTÄVÄ ---\n{step['task_prompt']}"
                
                with st.spinner(f"Suoritetaan {step['name']}..."):
                    try:
                        # Kutsu suoraan mallia tässä jotta saadaan UI päivitys
                        model = genai.GenerativeModel(selected_model)
                        response = model.generate_content(final_prompt)
                        result_text = response.text
                        results[step_id] = result_text
                        
                        # UI Logiikka
                        if step_id == "moodi_c":
                            st.subheader(step["name"])
                            # Yritetään erottaa raportti JSONista
                            if "Lopullinen Arviointiraportti" in result_text:
                                parts = result_text.split("Lopullinen Arviointiraportti")
                                json_part = parts[0]
                                report_part = "Lopullinen Arviointiraportti" + parts[1]
                                
                                with st.expander("Tekniset tiedot (JSON)"):
                                    st.code(json_part)
                                
                                st.markdown("### 📝 LOPULLINEN ARVIOINTIRAPORTTI")
                                st.markdown(report_part)
                            else:
                                st.markdown(result_text)
                        else:
                            # Välivaiheet piiloon
                            with st.expander(f"✅ {step['name']} (Klikkaa nähdäksesi yksityiskohdat)"):
                                st.markdown(result_text)
                                
                    except Exception as e:
                        st.error(f"Virhe vaiheessa {step['name']}: {str(e)}")
                        results[step_id] = f"VIRHE: {str(e)}"
                    
        st.success("Orkestrointi valmis!")

with tab2:
    if st.button("Käynnistä Agentti-ajot", type="primary", disabled=not uploaded_files):
        if not agents:
            st.error("Ei agentteja määriteltynä.")
        else:
            st.header("Tulokset")
            result_containers = {agent['name']: st.empty() for agent in agents}
            for agent in agents:
                with result_containers[agent['name']].container():
                    st.subheader(f"Agentti: {agent['name']}")
                    with st.spinner(f"Suoritetaan analyysiä..."):
                        result = processor.process_agent(agent, uploaded_files, model_name=model_selection)
                        st.markdown(result)
                        st.divider()
            st.success("Kaikki ajot suoritettu!")

