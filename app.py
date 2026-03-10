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
# 2. COMPACT SENIOR UI (CSS)
# ----------------------------------------------------------------
st.set_page_config(page_title="AI Research Agent | Zaid Suhail", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&family=JetBrains+Mono&display=swap');
    
    /* Minimize Whitespace & Global Background */
    .stApp { background: #0b0e14; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    
    /* Centered Branding - Reduced Spacing */
    .brand-container { text-align: center; margin-bottom: 1.5rem; }
    .hero-title {
        background: linear-gradient(90deg, #fff, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem; font-weight: 800; margin: 0;
    }
    .hero-sub { color: #8b949e; font-family: 'JetBrains Mono'; font-size: 0.85rem; letter-spacing: 1px; }

    /* Glass Cards */
    .glass-card {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 1.5rem; margin-bottom: 1rem;
    }

    /* Literature Review Box */
    .lit-review-box {
        background: #010409;
        border-left: 5px solid #00f2fe;
        padding: 20px; border-radius: 8px;
        line-height: 1.7; font-size: 1rem;
        color: #e6edf3; white-space: pre-wrap;
    }

    /* Citation Block */
    .citation-block {
        background: #161b22; border: 1px solid #30363d;
        padding: 15px; border-radius: 6px; margin-bottom: 15px;
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
            "illustrated", "quantified", "evaluated", "pioneered"
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
# 4. BRANDING (CENTERED & COMPACT)
# ----------------------------------------------------------------
st.markdown('<div class="brand-container">', unsafe_allow_html=True)
l_path = "media/logo.png" if os.path.exists("media/logo.png") else "logo.png"
if os.path.exists(l_path):
    st.image(l_path, width=120) # Reduced width for professional feel
st.markdown('<div class="hero-title">AI RESEARCH AGENT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">MUHAMMAD ZAID SUHAIL | APPLIED AI & ELECTRICAL ENGINEER</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 5. UNIFIED RESEARCH DASHBOARD
# ----------------------------------------------------------------
tab_main, tab_citations = st.tabs(["🚀 RESEARCH ENGINE", "📂 CITATION & LATEX GENERATOR"])

with tab_main:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([5, 2, 2])
    with c1: 
        query = st.text_input("Scientific Keyword Search", placeholder="e.g. 'Power System Stability LLM'", label_visibility="collapsed")
    with c2:
        style_choice = st.selectbox("Citation Style", ["IEEE", "Harvard"], label_visibility="collapsed")
    with c3:
        word_limit = st.select_slider("Words/Paper", [50, 100, 150, 200, 250], value=100)
    
    if st.button("🔍 Initialize Discovery"):
        if query:
            from data_pipeline.paper_ingestion import fetch_papers
            st.session_state.papers = fetch_papers(query, max_results=8)
            st.session_state.selected_ids = set()
            st.session_state.generated_review = ""
        else: st.warning("Please enter a research query.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.papers:
        col_list, col_gen = st.columns([1, 1])
        with col_list:
            st.subheader("📚 Results")
            for i, p in enumerate(st.session_state.papers):
                with st.container():
                    st.markdown(f"**{p['title']}**")
                    if st.checkbox(f"Add to Review", key=f"chk_{p['id']}"):
                        st.session_state.selected_ids.add(p['id'])
                    else:
                        st.session_state.selected_ids.discard(p['id'])
                    with st.expander("Abstract"):
                        st.write(p['summary'])
                        st.markdown(f"[arXiv Link](https://arxiv.org/abs/{p['id']})")
                    st.divider()

        with col_gen:
            st.subheader("✍️ Synthesis")
            if not st.session_state.selected_ids:
                st.info("Select papers to begin.")
            else:
                if st.button("✨ Generate Synthesis"):
                    from agents.summarizer_agent import generate_lit_review
                    full_review = ""
                    idx = 1
                    for p_id in st.session_state.selected_ids:
                        p_data = next(item for item in st.session_state.papers if item["id"] == p_id)
                        with st.spinner(f"Processing..."):
                            header = format_academic_line(p_data, style_choice, idx)
                            body = generate_lit_review(p_data['summary'], style=style_choice, word_count=word_limit)
                            full_review += f"{header} {body}\n\n"
                            idx += 1
                    st.session_state.generated_review = full_review

                if st.session_state.generated_review:
                    st.markdown(f'<div class="lit-review-box">{st.session_state.generated_review}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Download", st.session_state.generated_review, file_name="Report.txt")

# --- TAB 2: CITATION GENERATOR (DUAL MODE) ---
with tab_citations:
    mode = st.radio("Citation Mode:", ["Selected from Discovery", "Manually Paste URL"], horizontal=True)
    
    cite_papers = []
    
    if mode == "Selected from Discovery":
        if not st.session_state.selected_ids:
            st.warning("No papers selected in Tab 1.")
        else:
            for pid in st.session_state.selected_ids:
                cite_papers.append(next(item for item in st.session_state.papers if item["id"] == pid))
    else:
        manual_url = st.text_input("Paste arXiv URL (e.g., https://arxiv.org/abs/2301.00000)")
        if st.button("Fetch Manual Citation"):
            m_data = get_arxiv_meta(manual_url)
            if m_data: cite_papers.append(m_data)
            else: st.error("Could not fetch metadata.")

    if cite_papers:
        for i, p in enumerate(cite_papers):
            st.markdown(f'<div class="citation-block">', unsafe_allow_html=True)
            st.markdown(f"**Paper:** {p['title']}")
            
            # 1. Plain Text Citation
            if style_choice == "IEEE":
                txt = f"[{i+1}] {p['authors']}, \"{p['title']}\", arXiv:{p['id']}, {p.get('year','2026')}."
            else:
                txt = f"{p['authors'].split(',')[0]} ({p.get('year','2026')}). {p['title']}. Available at: https://arxiv.org/abs/{p['id']}"
            
            st.text_area("Plain Text Citation", txt, height=70, key=f"txt_{p['id']}")
            
            # 2. LaTeX Code
            bib = f"@article{{{p['id']},\n  title={{{p['title']}}},\n  author={{{p['authors']}}},\n  year={{{p.get('year','2026')}}},\n  journal={{arXiv preprint arXiv:{p['id']}}}\n}}"
            st.code(bib, language="latex")
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 6. FOOTER
# ----------------------------------------------------------------
st.markdown('<div style="text-align:center; padding:10px; font-size:0.8rem; color:#444;">Built by Zaid Suhail | 2026</div>', unsafe_allow_html=True)
