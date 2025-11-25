import streamlit as st
import json
import os
from llm_service import LLMService
from data_handler import DataHandler, TextUpload
from orchestrator import Orchestrator
from context import AssessmentContext
from prompt_splitter import PromptSplitter

# Sivun asetukset
st.set_page_config(page_title="Holistinen Mestaruus 3.0", layout="wide")
st.title("🤖 Holistinen Mestaruus 3.0")

# --- ALUSTUS (Service Layer & Data Layer) ---
try:
    llm_service = LLMService()
    data_handler = DataHandler()
    orchestrator = Orchestrator(llm_service, data_handler)
    api_key_configured = True
except ValueError:
    st.warning("API-avain puuttuu .env-tiedostosta. Syötä se sivupalkkiin.")
    api_key_configured = False
    # Fallback: luodaan dummy-palvelut jotta UI ei kaadu, mutta estetään ajot
    class DummyLLM:
        def get_available_models(self): return ["gemini-1.5-flash"]
        def generate_response(self, p, m): return "VIRHE: API-avain puuttuu."
    llm_service = DummyLLM()
    data_handler = DataHandler()
    orchestrator = Orchestrator(llm_service, data_handler)

# --- SIVUPALKKI (Configuration) ---
with st.sidebar:
    st.header("Asetukset")
    
    if not api_key_configured:
        api_key = st.text_input("Gemini API Key", type="password").strip()
        if api_key:
            os.environ["GOOGLE_API_KEY"] = api_key
            st.rerun()
            
    # Mallin valinta
    available_models = llm_service.get_available_models()
    default_index = 0
    if "gemini-2.5-flash" in available_models:
        default_index = available_models.index("gemini-2.5-flash")
    elif "gemini-1.5-flash-latest" in available_models:
        default_index = available_models.index("gemini-1.5-flash-latest")
    elif "gemini-1.5-flash" in available_models:
        default_index = available_models.index("gemini-1.5-flash")
        
    model_selection = st.selectbox("Valitse malli", available_models, index=default_index)
    
    st.subheader("Agentit")
    try:
        with open(os.path.join(os.path.dirname(__file__), 'agents.json'), 'r', encoding='utf-8') as f:
            agents = json.load(f)
        st.success(f"Ladattu {len(agents)} agenttia.")
    except FileNotFoundError:
        st.error("agents.json ei löytynyt!")
        agents = []

# --- PÄÄALUE (Presentation Layer) ---

st.header("1. Lataa tiedostot")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Keskusteluhistoria")
    historia_mode = st.radio("Syöttötapa", ["Lataa tiedosto", "Liitä teksti"], label_visibility="collapsed")
    
    historia_file = None
    if historia_mode == "Lataa tiedosto":
        historia_file = st.file_uploader("Lataa PDF/TXT", type=['pdf', 'txt'], label_visibility="collapsed")
    else:
        historia_text = st.text_area("Liitä keskustelu tähän (Ctrl+V)", height=150)
        if historia_text:
            historia_file = TextUpload(historia_text)

with col2:
    st.markdown("### Lopputuote")
    lopputuote_file = st.file_uploader("Lataa PDF/TXT", type=['pdf', 'txt'], key="lopputuote")
with col3:
    st.markdown("### Reflektio")
    reflektio_file = st.file_uploader("Lataa PDF/TXT", type=['pdf', 'txt'], key="reflektio")

uploaded_files = [f for f in [historia_file, lopputuote_file, reflektio_file] if f is not None]

# --- KEHOTTEEN LATAUS ---
st.subheader("Pääarviointikehote")
custom_prompt_file = st.file_uploader("Lataa uusi Pääarviointikehote (DOCX)", type=['docx'])

prompt_data = (None, None) # (common_rules, phases_dict)
prompt_source_path = None

import tempfile

if custom_prompt_file:
    # Tallenna ladattu tiedosto väliaikaisesti (käytä tempfileä pilviyhteensopivuuden takia)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp_file:
        tmp_file.write(custom_prompt_file.getbuffer())
        prompt_source_path = tmp_file.name
    
    # Jaa dokumentti osiin
    splitter = PromptSplitter(prompt_source_path)
    splitter.split_document()
    
    # Siivoa väliaikaistiedosto
    try:
        os.remove(prompt_source_path)
    except:
        pass
    
    # Lataa jaetut moduulit
    prompt_modules = splitter.get_prompt_modules()
    common_rules = prompt_modules.get('COMMON_RULES', '')
    prompt_phases = {k: v for k, v in prompt_modules.items() if k.startswith('VAIHE')}
    prompt_data = (common_rules, prompt_phases)
    
    st.success("✅ Käytetään ladattua Pääarviointikehotetta (Jaettu osiin).")
else:
    # Fallback: Käytä oletustiedostoa
    prompt_path = os.path.join(os.getcwd(), "Pääarviointikehote.docx")
    if os.path.exists(prompt_path):
        prompt_source_path = prompt_path
        
        # Jaa dokumentti osiin
        splitter = PromptSplitter(prompt_path)
        splitter.split_document()
        
        # Lataa jaetut moduulit
        prompt_modules = splitter.get_prompt_modules()
        common_rules = prompt_modules.get('COMMON_RULES', '')
        prompt_phases = {k: v for k, v in prompt_modules.items() if k.startswith('VAIHE')}
        prompt_data = (common_rules, prompt_phases)
        
        st.info(f"ℹ️ Käytetään oletuskehotetta (Jaettu osiin).")
    else:
        st.warning(f"⚠️ Pääarviointikehote.docx ei löytynyt kansiosta.")
        common_rules, prompt_phases = None, None

if common_rules and prompt_phases:
    with st.expander("📊 Kehotteen tilastot"):
        st.write(f"Yleiset säännöt: {len(common_rules):,} merkkiä (~{len(common_rules)//4:,} tokenia)")
        st.write(f"Vaiheita: {len(prompt_phases)}")
        total_phase_chars = sum(len(v) for v in prompt_phases.values())
        st.write(f"Vaihe-ohjeet yhteensä: {total_phase_chars:,} merkkiä (~{total_phase_chars//4:,} tokenia)")

# --- ORKESTROINTI ---
tab1, tab2 = st.tabs(["Orkestrointi (9 Vaihetta)", "Yksittäiset Agentit"])

with tab1:
    st.info("Suorittaa arviointiprosessin.")
    
    execution_mode = st.radio("Suoritustapa", ["Koko Prosessi (Vaiheet 1-9)", "Vaiheittainen (Moodit A, B, C)"])
    
    # Alusta konteksti (jos ei jo olemassa session statessa, jotta data säilyy moodien välillä)
    if "assessment_context" not in st.session_state:
        st.session_state.assessment_context = None

    if st.button("Alusta / Nollaa Konteksti", type="secondary"):
        st.session_state.assessment_context = AssessmentContext(common_rules, prompt_phases)
        # Lisää tiedostot
        for uploaded_file in uploaded_files:
            content = data_handler.read_file_content(uploaded_file)
            st.session_state.assessment_context.add_file(uploaded_file.name, content)
        st.success("Konteksti alustettu!")

    context = st.session_state.assessment_context
    
    if execution_mode == "Koko Prosessi (Vaiheet 1-9)":
        if st.button("Käynnistä Koko Orkestrointi", type="primary", disabled=not context):
            st.header("Tulokset")
            phases = orchestrator.get_phases()
            results_placeholders = {step['id']: st.empty() for step in phases}
            
            # Debug: Näytä mitä vaiheita tunnistettiin
            with st.expander("ℹ️ Debug: Tunnistetut vaiheet"):
                st.write(f"Yleiset säännöt: {len(common_rules)} merkkiä")
                st.write(list(prompt_phases.keys()))

            for step in phases:
                step_id = step["id"]
                with results_placeholders[step_id].container():
                    with st.spinner(f"Suoritetaan {step['name']}..."):
                        
                        # Debug: Näytä kehote ennen lähetystä (paitsi Vaihe 9, joka on Python-koodia)
                        if step_id != "phase_9":
                            phase_key = step.get("phase_key")
                            debug_prompt = context.build_prompt(phase_key)
                            with st.expander(f"🔍 Debug: Kehote ({step['name']})"):
                                st.text(debug_prompt)
                            
                        result_text = orchestrator.run_phase(
                            step_id, 
                            context, 
                            model_selection
                        )
                        
                        with st.expander(f"✅ {step['name']} (Valmis)"):
                            st.markdown(result_text)
            st.success("Koko prosessi valmis!")

    else: # Vaiheittainen (Moodit A, B, C)
        st.markdown("---")
        
        if not context:
            st.warning("⚠️ Sinun täytyy alustaa konteksti ensin painamalla yllä olevaa 'Alusta / Nollaa Konteksti' -painiketta, jotta voit suorittaa moodeja.")
        
        # MOODI A
        st.subheader("Moodi A: Alustus (Vaiheet 1-3)")
        if st.button("Suorita Moodi A", type="primary", disabled=not context):
            with st.spinner("Suoritetaan Moodi A..."):
                results = orchestrator.run_mode("MOODI_A", context, model_selection)
                for pid, res in results.items():
                    st.markdown(f"**{pid}**: Valmis")
                    with st.expander(f"Tulos: {pid}"):
                        st.markdown(res)
            st.success("Moodi A valmis!")

        st.markdown("---")

        # MOODI B
        st.subheader("Moodi B: Auditointi (Vaiheet 4-7)")
        if st.button("Suorita Moodi B", type="primary", disabled=not context):
             with st.spinner("Suoritetaan Moodi B..."):
                results = orchestrator.run_mode("MOODI_B", context, model_selection)
                for pid, res in results.items():
                    st.markdown(f"**{pid}**: Valmis")
                    with st.expander(f"Tulos: {pid}"):
                        st.markdown(res)
             st.success("Moodi B valmis!")

        st.markdown("---")

        # MOODI C
        st.subheader("Moodi C: Synteesi (Vaiheet 8-9)")
        if st.button("Suorita Moodi C", type="primary", disabled=not context):
             with st.spinner("Suoritetaan Moodi C..."):
                results = orchestrator.run_mode("MOODI_C", context, model_selection)
                for pid, res in results.items():
                    st.markdown(f"**{pid}**: Valmis")
                    with st.expander(f"Tulos: {pid}"):
                        st.markdown(res)
             st.success("Moodi C valmis!")

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
                        result = orchestrator.run_agent(agent, uploaded_files, model_selection)
                        st.markdown(result)
                        st.divider()
            st.success("Kaikki ajot suoritettu!")
