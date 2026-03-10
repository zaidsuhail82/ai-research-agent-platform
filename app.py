import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import random
from datetime import datetime

# ----------------------------------------------------------------
# 1. ANALYTICS & STATE MANAGEMENT
# ----------------------------------------------------------------
if 'papers' not in st.session_state: st.session_state.papers = []
if 'selected_ids' not in st.session_state: st.session_state.selected_ids = set()
if 'generated_review' not in st.session_state: st.session_state.generated_review = ""

# ----------------------------------------------------------------
# 2. COMPACT & CENTERED UI (CSS)
# ----------------------------------------------------------------
# Note: favicon set here
l_path = "media/logo.png" if os.path.exists("media/logo.png") else "logo.png"
st.set_page_config(
    page_title="AI Research Agent | Zaid Suhail", 
    page_icon=l_path if os.path.exists(l_path) else None,
    layout="wide"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap');
    
    .stApp { background: #0b0e14; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem !important; }
    
    /* Centered Branding */
    .brand-container { 
        display: flex; flex-direction: column; align-items: center; 
        text-align: center; margin-bottom: 1.5rem; 
    }
    .hero-title {
        background: linear-gradient(90deg, #fff, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem; font-weight: 800; margin: 5px 0;
    }
    .hero-sub { color: #8b949e; font-family: 'JetBrains Mono'; font-size: 0.85rem; letter-spacing: 1px; }

    /* Forms and Inputs */
    .stForm { border: none !important; padding: 0 !important; }
    
    /* Literature Review Box */
    .lit-review-box {
        background: #010409;
        border-left: 5px solid #00f2fe;
        padding: 20px; border-radius: 8px;
        line-height: 1.7; font-size: 1rem;
        color: #e6edf3; white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------
# 3. SCIENTIFIC AGENT UTILITIES
# ----------------------------------------------------------------

class ScientificLexicon:
    @staticmethod
    def get_verb():
        return random.choice([
            "pioneered", "formulated", "scrutinized", "elucidated", 
            "analyzed", "demonstrated", "implemented", "developed", 
            "illustrated", "quantified", "evaluated"
        ])

def format_academic_line(paper, style, index):
    authors = [a.strip() for a in paper.get('authors', 'Unknown').split(',')]
    last_name = authors[0].split(' ')[-1]
    initial = authors[0][0]
    year = paper.get('year', '2026')
    verb = ScientificLexicon.get_verb()
    et_al = " et al." if len(authors) > 1 else ""

    if style == "IEEE":
        return f"{last_name}, {initial}. [{index}] {verb}"
    else:
        return f"{last_name}, {initial}.{et_al} ({year}) {verb}"

def get_arxiv_meta(url):
    try:
        pid = url.split('/')[-1].replace('.pdf', '')
        api = f"http://export.arxiv.org/api/query?id_list={pid}"
        r = requests.get(api, timeout=5)
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        return {
            "title": entry.find('atom:title', ns).text.strip().replace('\n', ' '),
            "authors": ", ".join([a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]),
            "year": entry.find('atom:published', ns).text[:4],
            "id": pid
        }
    except: return None

# ----------------------------------------------------------------
# 4. BRANDING (CENTERED)
# ----------------------------------------------------------------
st.markdown('<div class="brand-container">', unsafe_allow_html=True)
if os.path.exists(l_path):
    st.image(l_path, width=100)
st.markdown('<div class="hero-title">AI RESEARCH AGENT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">MUHAMMAD ZAID SUHAIL | APPLIED AI & ELECTRICAL ENGINEER</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 5. UNIFIED RESEARCH DASHBOARD
# ----------------------------------------------------------------
tab_main, tab_citations = st.tabs(["🚀 RESEARCH ENGINE", "📂 CITATION & LATEX"])

with tab_main:
    # --- SEARCH FORM (Allows Enter to Search) ---
    with st.form("search_form", clear_on_submit=False):
        c1, c2, c3 = st.columns([5, 2, 2])
        with c1: 
            query = st.text_input("Scientific Keyword Search", placeholder="Type keywords and press Enter...")
        with c2:
            style_choice = st.selectbox("Style", ["IEEE", "Harvard"])
        with c3:
            word_limit = st.select_slider("Words", [50, 100, 150, 200, 250], value=100)
        
        search_submitted = st.form_submit_button("🔍 Initialize Discovery")
        
        if search_submitted:
            if query:
                from data_pipeline.paper_ingestion import fetch_papers
                st.session_state.papers = fetch_papers(query, max_results=8)
                st.session_state.selected_ids = set() # Reset on new search
                st.session_state.generated_review = ""
            else:
                st.warning("Please enter keywords.")

    if st.session_state.papers:
        col_list, col_gen = st.columns([1, 1])
        
        with col_list:
            st.subheader("📚 Discovery Results")
            for p in st.session_state.papers:
                # Checkbox selection logic
                checked = st.checkbox(f"Add: {p['title'][:60]}...", key=f"chk_{p['id']}", 
                                     value=p['id'] in st.session_state.selected_ids)
                if checked:
                    st.session_state.selected_ids.add(p['id'])
                else:
                    st.session_state.selected_ids.discard(p['id'])
                
                with st.expander("Abstract & Details"):
                    st.write(p['summary'])
                    st.markdown(f"**ID:** {p['id']} | [arXiv Link](https://arxiv.org/abs/{p['id']})")
                st.divider()

        with col_gen:
            st.subheader("✍️ Literature Synthesis")
            if not st.session_state.selected_ids:
                st.info("Check papers on the left to begin synthesis.")
            else:
                if st.button("✨ Generate Synthesis"):
                    from agents.summarizer_agent import generate_lit_review
                    full_review = ""
                    idx = 1
                    # Iterate through the papers in the order they appear in the results
                    selected_data = [p for p in st.session_state.papers if p['id'] in st.session_state.selected_ids]
                    
                    for p_data in selected_data:
                        with st.spinner(f"Synthesizing {p_data['id']}..."):
                            header = format_academic_line(p_data, style_choice, idx)
                            body = generate_lit_review(p_data['summary'], style=style_choice, word_count=word_limit)
                            full_review += f"{header} {body}\n\n"
                            idx += 1
                    st.session_state.generated_review = full_review

                if st.session_state.generated_review:
                    st.markdown(f'<div class="lit-review-box">{st.session_state.generated_review}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Download Report", st.session_state.generated_review, file_name="Zaid_Research.txt")

# --- TAB 2: CITATION GENERATOR ---
with tab_citations:
    mode = st.radio("Mode:", ["Discovery Selection", "Manual URL"], horizontal=True)
    
    cite_list = []
    if mode == "Discovery Selection":
        cite_list = [p for p in st.session_state.papers if p['id'] in st.session_state.selected_ids]
    else:
        manual_url = st.text_input("arXiv URL:")
        if st.button("Fetch Citation"):
            m = get_arxiv_meta(manual_url)
            if m: cite_list.append(m)

    for i, p in enumerate(cite_list):
        st.markdown(f"### Reference: {p['title']}")
        if style_choice == "IEEE":
            cite_text = f"[{i+1}] {p['authors']}, \"{p['title']}\", arXiv:{p['id']}, 2026."
        else:
            cite_text = f"{p['authors'].split(',')[0]} (2026). {p['title']}. Available at: https://arxiv.org/abs/{p['id']}"
        
        st.code(cite_text, language="text")
        st.code(f"@article{{{p['id']},\n  title={{{p['title']}}},\n  author={{{p['authors']}}},\n  year={{2026}}\n}}", language="latex")
        st.divider()

st.markdown('<div style="text-align:center; padding-top:20px; color:#444;">Developed by Zaid Suhail | 2026</div>', unsafe_allow_html=True)
