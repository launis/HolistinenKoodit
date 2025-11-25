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
            
            st.rerun()

    # Google Search API asetukset (Faktantarkistus)
    search_api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    search_cx = os.getenv("GOOGLE_SEARCH_CX")

    if not search_api_key or not search_cx:
        with st.expander("Faktantarkistuksen asetukset"):
            st.caption("Tarvitaan Vaiheen 7 faktantarkistukseen.")
            
            if not search_api_key:
                new_search_key = st.text_input("Google Search API Key", type="password", key="search_key_input").strip()
                if new_search_key:
                    os.environ["GOOGLE_SEARCH_API_KEY"] = new_search_key
                    st.rerun()
            
            if not search_cx:
                new_cx = st.text_input("Google Search CX ID", type="password", key="search_cx_input").strip()
                if new_cx:
                    os.environ["GOOGLE_SEARCH_CX"] = new_cx
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
        
    model_selection = st.selectbox("Valitse Päämalli (Analyysi & Synteesi)", available_models, index=default_index)
    
    # Kriitikkoryhmän malli (Phases 4-7)
    st.caption("Kriitikkoryhmän malli (Vaiheet 4-7)")
    critic_model_selection = st.selectbox(
        "Valitse Kriitikkomalli", 
        available_models, 
        index=default_index,
        help="Voit valita eri mallin kriitikkoryhmälle (Red Teaming) parantaaksesi luotettavuutta."
    )
    
    # Tutkimusdatan keräys (Luku 6.2)
    st.caption("Tutkimusagenda (Luku 6)")
    collect_dataset = st.checkbox(
        "Kerää tutkimusdataa (Dataset)", 
        value=True, 
        help="Jos valittu, tallentaa raakadatan (JSON + Scratchpad) dataset/ -kansioon tulevaa tislausta varten."
    )
    
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
    # 1. Yritä ladata valmiit tekstitiedostot (Prompts-kansio on LAKI)
    prompts_dir = os.path.join(os.getcwd(), "prompts")
    splitter = PromptSplitter() # Ei tarvitse lähdetiedostoa jos ladataan levyltä
    
    if splitter.load_from_disk(prompts_dir):
        st.success("✅ Käytetään muokattuja kehotteita (prompts-kansiosta).")
        
        # Lataa moduulit
        prompt_modules = splitter.get_prompt_modules()
        common_rules = prompt_modules.get('COMMON_RULES', '')
        prompt_phases = {k: v for k, v in prompt_modules.items() if k.startswith('VAIHE')}
        prompt_data = (common_rules, prompt_phases)
        
    else:
        # 2. Fallback: Jos ei löydy, yritä parsia DOCX
        prompt_path = os.path.join(os.getcwd(), "Pääarviointikehote.docx")
        if os.path.exists(prompt_path):
            splitter = PromptSplitter(prompt_path)
            if splitter.split_document():
                splitter.save_to_disk() # Tallenna tulevaa käyttöä varten
                
                prompt_modules = splitter.get_prompt_modules()
                common_rules = prompt_modules.get('COMMON_RULES', '')
                prompt_phases = {k: v for k, v in prompt_modules.items() if k.startswith('VAIHE')}
                prompt_data = (common_rules, prompt_phases)
                
                st.info(f"ℹ️ Luettiin ja jaettiin Pääarviointikehote.docx.")
            else:
                st.error("Virhe dokumentin jakamisessa.")
        else:
            st.warning(f"⚠️ Kehotteita ei löytynyt (ei prompts-kansiota eikä .docx-tiedostoa).")
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
    
    # Alusta tulosmuuttujat session statessa
    if "full_process_results" not in st.session_state:
        st.session_state.full_process_results = None
    if "mode_a_results" not in st.session_state:
        st.session_state.mode_a_results = None
    if "mode_b_results" not in st.session_state:
        st.session_state.mode_b_results = None
    if "mode_c_results" not in st.session_state:
        st.session_state.mode_c_results = None
    if "pdf_path" not in st.session_state:
        st.session_state.pdf_path = None

    if st.button("Alusta / Nollaa Konteksti", type="secondary"):
        st.session_state.assessment_context = AssessmentContext(common_rules, prompt_phases)
        # Lisää tiedostot
        # Lisää tiedostot
        if historia_file:
            content = data_handler.read_file_content(historia_file)
            st.session_state.assessment_context.add_file("Keskusteluhistoria.pdf", content)
            
        if lopputuote_file:
            content = data_handler.read_file_content(lopputuote_file)
            st.session_state.assessment_context.add_file("Lopputuote.pdf", content)
            
        if reflektio_file:
            content = data_handler.read_file_content(reflektio_file)
            st.session_state.assessment_context.add_file("Reflektiodokumentti.pdf", content)
            
        st.success("Konteksti alustettu! Tiedostot ladattu muistiin.")

    context = st.session_state.assessment_context
    
    if execution_mode == "Koko Prosessi (Vaiheet 1-9)":
        if st.button("Käynnistä Koko Orkestrointi", type="primary", disabled=not context):
            st.session_state.full_process_results = {} # Reset
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
                            
                        # Valitse malli vaiheen mukaan
                        current_model = model_selection
                        if step_id in ["phase_4", "phase_5", "phase_6", "phase_7"]:
                            current_model = critic_model_selection
                            
                        result_text = orchestrator.run_phase(
                            step_id, 
                            context, 
                            current_model,
                            save_dataset=collect_dataset
                        )
                        
                        # Tallenna tulos sessioon
                        st.session_state.full_process_results[step_id] = result_text
                        
                        with st.expander(f"✅ {step['name']} (Valmis)"):
                            st.markdown(result_text)
            
            # PDF-lataus (Koko Prosessi)
            if "phase_9" in orchestrator.results:
                report_content = orchestrator.results["phase_9"]
                pdf_filename = "Holistinen_Mestaruus_Raportti.pdf"
                
                # Luo PDF
                saved_file = orchestrator.report_generator.save_as_pdf(report_content, pdf_filename)
                st.session_state.pdf_path = saved_file

        # Näytä tulokset (jos olemassa session statessa)
        if st.session_state.full_process_results:
             st.success("Koko prosessi valmis!")
             
             # Näytä aiemmat tulokset (valinnainen, tässä näytetään vain PDF-lataus selkeyden vuoksi)
             # Mutta HITL tarvitaan
             
             if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
                # HITL: Ihmisvalvonta
                st.markdown("### 🛡️ Hallinnollinen Kontrolli (HITL)")
                hitl_confirmed = st.checkbox("✅ Vahvistan tarkistaneeni tulokset ja hyväksyn raportin lataamisen.", key="hitl_full")
                
                if hitl_confirmed:
                    with open(st.session_state.pdf_path, "rb") as f:
                        pdf_data = f.read()
                    st.download_button(
                        label="📄 Lataa Raportti (PDF)",
                        data=pdf_data,
                        file_name="Holistinen_Mestaruus_Raportti.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("⚠️ Sinun täytyy vahvistaa tulokset ennen lataamista.")

    else: # Vaiheittainen (Moodit A, B, C)
        st.markdown("---")
        
        if not context:
            st.warning("⚠️ Sinun täytyy alustaa konteksti ensin painamalla yllä olevaa 'Alusta / Nollaa Konteksti' -painiketta, jotta voit suorittaa moodeja.")
        
        # MOODI A
        st.subheader("Moodi A: Alustus (Vaiheet 1-3)")
        if st.button("Suorita Moodi A", type="primary", disabled=not context):
            with st.spinner("Suoritetaan Moodi A..."):
                results = orchestrator.run_mode("MOODI_A", context, model_selection, save_dataset=collect_dataset)
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
                results = orchestrator.run_mode("MOODI_B", context, model_selection, critic_model_name=critic_model_selection, save_dataset=collect_dataset)
                st.session_state.mode_b_results = results
                
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
                results = orchestrator.run_mode("MOODI_C", context, model_selection, save_dataset=collect_dataset)
                st.session_state.mode_c_results = results
                
                for pid, res in results.items():
                    st.markdown(f"**{pid}**: Valmis")
                    with st.expander(f"Tulos: {pid}"):
                        st.markdown(res)
                        
                # PDF-lataus
                if "phase_9" in results:
                    report_content = results["phase_9"]
                    pdf_filename = "Holistinen_Mestaruus_Raportti.pdf"
                    
                    # Luo PDF
                    saved_file = orchestrator.report_generator.save_as_pdf(report_content, pdf_filename)
                    st.session_state.pdf_path = saved_file

        if st.session_state.mode_c_results:
             st.success("Moodi C valmis!")
             
             if st.session_state.pdf_path and os.path.exists(st.session_state.pdf_path):
                # HITL: Ihmisvalvonta
                st.markdown("### 🛡️ Hallinnollinen Kontrolli (HITL)")
                hitl_confirmed_c = st.checkbox("✅ Vahvistan tarkistaneeni tulokset ja hyväksyn raportin lataamisen.", key="hitl_mode_c")
                
                if hitl_confirmed_c:
                    with open(st.session_state.pdf_path, "rb") as f:
                        pdf_data = f.read()
                    st.download_button(
                        label="📄 Lataa Raportti (PDF)",
                        data=pdf_data,
                        file_name="Holistinen_Mestaruus_Raportti.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("⚠️ Sinun täytyy vahvistaa tulokset ennen lataamista.")

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
