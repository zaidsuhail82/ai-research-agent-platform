import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import random
from datetime import datetime

# ----------------------------------------------------------------
# 1. CORE CONFIG & FAVICON
# ----------------------------------------------------------------
l_path = "media/logo.png" if os.path.exists("media/logo.png") else "logo.png"
st.set_page_config(
    page_title="AI Research Agent | Zaid Suhail", 
    page_icon=l_path if os.path.exists(l_path) else "🔖",
    layout="wide"
)

# Initialize Session State
if 'papers' not in st.session_state: st.session_state.papers = []
if 'selected_ids' not in st.session_state: st.session_state.selected_ids = set()
if 'generated_review' not in st.session_state: st.session_state.generated_review = ""

# ----------------------------------------------------------------
# 2. CENTERED UI & COMPACT STYLING
# ----------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap');
    
    .stApp { background: #0b0e14; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1rem !important; }
    
    .brand-container { 
        display: flex; flex-direction: column; align-items: center; 
        text-align: center; margin-bottom: 1rem; 
    }
    .hero-title {
        background: linear-gradient(90deg, #fff, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem; font-weight: 800; margin: 0;
    }
    .hero-sub { color: #8b949e; font-family: 'JetBrains Mono'; font-size: 0.8rem; letter-spacing: 1px; }

    /* Fix White Borders on Inputs */
    .stTextInput>div>div>input { background-color: #161b22; color: white; border: 1px solid #30363d; }
    
    /* Result Boxes */
    .lit-review-box {
        background: #010409;
        border-left: 4px solid #00f2fe;
        padding: 20px; border-radius: 8px;
        line-height: 1.7; font-size: 1rem;
        color: #e6edf3; white-space: pre-wrap;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------
# 3. SCIENTIFIC AGENT UTILITIES (ERROR-PROOFED)
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
    """Hardened formatter to prevent AttributeError on authors."""
    raw_authors = paper.get('authors')
    if not raw_authors or not isinstance(raw_authors, str):
        authors = ["Unknown Researcher"]
    else:
        authors = [a.strip() for a in raw_authors.split(',')]
    
    # Extract Last Name and First Initial
    first_author_full = authors[0]
    name_parts = first_author_full.split(' ')
    last_name = name_parts[-1] if name_parts else "Researcher"
    initial = name_parts[0][0] if name_parts[0] else "R"
    
    year = paper.get('year', '2026')
    verb = ScientificLexicon.get_verb()
    et_al = " et al." if len(authors) > 1 else ""

    if style == "IEEE":
        # IEEE: Lastname, I. [index] verb...
        return f"{last_name}, {initial}. [{index}] {verb}"
    else:
        # Harvard: Lastname, I. et al. (year) verb...
        return f"{last_name}, {initial}.{et_al} ({year}) {verb}"

def get_arxiv_meta(url):
    try:
        pid = url.split('/')[-1].replace('.pdf', '')
        api = f"http://export.arxiv.org/api/query?id_list={pid}"
        r = requests.get(api, timeout=5)
        root = ET.fromstring(r.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is None: return None
        return {
            "title": entry.find('atom:title', ns).text.strip().replace('\n', ' '),
            "authors": ", ".join([a.find('atom:name', ns).text for a in entry.findall('atom:author', ns)]),
            "year": entry.find('atom:published', ns).text[:4],
            "summary": entry.find('atom:summary', ns).text.strip(),
            "id": pid
        }
    except Exception: return None

# ----------------------------------------------------------------
# 4. CENTERED BRANDING
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
    # --- SEARCH SECTION (ENTER TO SEARCH WORKS HERE) ---
    with st.form("main_search"):
        c1, c2, c3 = st.columns([5, 2, 2])
        with c1: 
            query = st.text_input("Scientific Keyword Search", placeholder="Type keywords and press Enter...")
        with c2:
            style_choice = st.selectbox("Style", ["IEEE", "Harvard"])
        with c3:
            word_limit = st.select_slider("Words", [50, 100, 150, 200, 250], value=100)
        
        submitted = st.form_submit_button("🔍 Search & Refresh")
        if submitted:
            if query:
                from data_pipeline.paper_ingestion import fetch_papers
                st.session_state.papers = fetch_papers(query, max_results=8)
                st.session_state.selected_ids = set()
                st.session_state.generated_review = ""
                st.rerun()

    if st.session_state.papers:
        col_list, col_gen = st.columns([1, 1])
        
        with col_list:
            st.subheader("📚 Discovery Results")
            for p in st.session_state.papers:
                # Maintain selection via session state
                is_selected = p['id'] in st.session_state.selected_ids
                if st.checkbox(f"{p['title'][:65]}...", key=f"chk_{p['id']}", value=is_selected):
                    st.session_state.selected_ids.add(p['id'])
                else:
                    st.session_state.selected_ids.discard(p['id'])
                
                with st.expander("Show Abstract"):
                    st.write(p['summary'])
                    st.markdown(f"[arXiv: {p['id']}](https://arxiv.org/abs/{p['id']})")
                st.divider()

        with col_gen:
            st.subheader("✍️ Literature Synthesis")
            if not st.session_state.selected_ids:
                st.info("Select papers on the left.")
            else:
                if st.button("✨ Generate Synthesis"):
                    from agents.summarizer_agent import generate_lit_review
                    full_review = ""
                    idx = 1
                    # Process selected papers
                    selected_data = [p for p in st.session_state.papers if p['id'] in st.session_state.selected_ids]
                    for p_data in selected_data:
                        with st.spinner(f"Analyzing {p_data['id']}..."):
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
    col_c1, col_c2 = st.columns([1, 1])
    
    with col_c1:
        st.subheader("Selected Discovery")
        discovery_cite = [p for p in st.session_state.papers if p['id'] in st.session_state.selected_ids]
        if not discovery_cite: st.info("No papers selected.")
        for i, p in enumerate(discovery_cite):
            st.markdown(f"**{p['title']}**")
            cite = f"[{i+1}] {p['authors']}, \"{p['title']}\", arXiv:{p['id']}, 2026." if style_choice == "IEEE" else f"{p['authors'].split(',')[0]} (2026). {p['title']}. Available at: https://arxiv.org/abs/{p['id']}"
            st.code(cite, language="text")
            st.code(f"@article{{{p['id']},\n  title={{{p['title']}}},\n  author={{{p['authors']}}},\n  year={{2026}}\n}}", language="latex")
            st.divider()

    with col_c2:
        st.subheader("Manual Citation")
        m_url = st.text_input("Paste arXiv URL:")
        if st.button("Generate Standalone"):
            m_data = get_arxiv_meta(m_url)
            if m_data:
                st.success("Fetched!")
                st.markdown(f"**{m_data['title']}**")
                st.code(f"{m_data['authors']}, \"{m_data['title']}\", 2026.", language="text")
                st.code(f"@article{{{m_data['id']},\n  title={{{m_data['title']}}},\n  author={{{m_data['authors']}}},\n  year={{2026}}\n}}", language="latex")

st.markdown('<div style="text-align:center; padding-top:20px; color:#444;">Developed by Zaid Suhail | 2026</div>', unsafe_allow_html=True)
