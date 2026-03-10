import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import random
import re
from datetime import datetime

# ----------------------------------------------------------------
# 1. ANALYTICS & STATE MANAGEMENT
# ----------------------------------------------------------------
if 'papers' not in st.session_state: st.session_state.papers = []
if 'selected_ids' not in st.session_state: st.session_state.selected_ids = set()
if 'generated_review' not in st.session_state: st.session_state.generated_review = ""

# ----------------------------------------------------------------
# 2. SENIOR RESEARCHER UI (CSS)
# ----------------------------------------------------------------
st.set_page_config(page_title="AI Research Agent | Zaid Suhail", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono&display=swap');
    
    .stApp { background: #0b0e14; color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Center Branding */
    .brand-container { text-align: center; padding: 2rem 0; }
    .hero-title {
        background: linear-gradient(90deg, #fff, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem; font-weight: 800; margin-bottom: 0;
    }
    .hero-sub { color: #8b949e; font-family: 'JetBrains Mono'; letter-spacing: 2px; }

    /* Glass Cards */
    .glass-card {
        background: rgba(22, 27, 34, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 25px; margin-bottom: 20px;
    }

    /* Literature Review Box */
    .lit-review-box {
        background: #010409;
        border-left: 5px solid #00f2fe;
        padding: 30px; border-radius: 8px;
        line-height: 1.9; font-size: 1.1rem;
        color: #e6edf3; white-space: pre-wrap;
        box-shadow: 0 4px 20px rgba(0,0,0,0.4);
    }

    /* Citation Generator Tab Styling */
    .citation-item {
        background: rgba(255,255,255,0.03);
        padding: 15px; border-radius: 8px; margin-bottom: 10px;
        font-family: 'JetBrains Mono', monospace; font-size: 0.9rem;
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
    """Scientific Citation Engine for Senior Engineers."""
    authors = [a.strip() for a in paper.get('authors', 'Unknown').split(',')]
    first_author_parts = authors[0].split(' ')
    last_name = first_author_parts[-1]
    initial = first_author_parts[0][0]
    
    year = paper.get('year', '2026')
    verb = ScientificLexicon.get_verb()
    et_al = " et al." if len(authors) > 1 else ""

    if style == "IEEE":
        # Format: Lastname, I. [index] verb...
        return f"{last_name}, {initial}. [{index}] {verb}"
    else:
        # Format: Lastname, I. et al. (year) verb...
        return f"{last_name}, {initial}.{et_al} ({year}) {verb}"

# ----------------------------------------------------------------
# 4. CENTERED BRANDING
# ----------------------------------------------------------------
st.markdown('<div class="brand-container">', unsafe_allow_html=True)
logo_path = "media/logo.png" if os.path.exists("media/logo.png") else "logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=280)
st.markdown('<div class="hero-title">AI RESEARCH AGENT</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">MUHAMMAD ZAID SUHAIL | APPLIED AI & ELECTRICAL ENGINEER</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 5. UNIFIED RESEARCH DASHBOARD
# ----------------------------------------------------------------
tab_main, tab_citations = st.tabs(["🚀 RESEARCH ENGINE", "📂 CITATION GENERATOR"])

with tab_main:
    # --- SEARCH SECTION ---
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([5, 2, 2])
    with c1: 
        query = st.text_input("Scientific Keyword Search", placeholder="e.g. 'Power System Stability LLM'")
    with c2:
        style_choice = st.selectbox("Citation Style", ["IEEE", "Harvard"])
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

    # --- RESULTS & SYNTHESIS ---
    if st.session_state.papers:
        col_list, col_gen = st.columns([1, 1])
        
        with col_list:
            st.subheader("📚 Discovery Results")
            for i, p in enumerate(st.session_state.papers):
                with st.container():
                    st.markdown(f"""
                    <div style="background:rgba(255,255,255,0.05); padding:15px; border-radius:10px; margin-bottom:10px;">
                        <b>{p['title']}</b><br>
                        <small>{p['authors']} | ID: {p['id']}</small>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Selection Logic
                    is_selected = st.checkbox(f"Add to Literature Review", key=f"chk_{p['id']}")
                    if is_selected:
                        st.session_state.selected_ids.add(p['id'])
                    else:
                        st.session_state.selected_ids.discard(p['id'])
                    
                    with st.expander("View Abstract"):
                        st.write(p['summary'])
                        st.markdown(f"[Link to ArXiv](https://arxiv.org/abs/{p['id']})")

        with col_gen:
            st.subheader("✍️ Live Literature Review")
            if not st.session_state.selected_ids:
                st.info("Select papers on the left to generate the synthesis.")
            else:
                if st.button("✨ Generate Synthesis Now"):
                    from agents.summarizer_agent import generate_lit_review
                    full_review = ""
                    idx = 1
                    for p_id in st.session_state.selected_ids:
                        # Find paper data in list
                        paper_data = next(item for item in st.session_state.papers if item["id"] == p_id)
                        with st.spinner(f"Synthesizing paper {idx}..."):
                            header = format_academic_line(paper_data, style_choice, idx)
                            body = generate_lit_review(paper_data['summary'], style=style_choice, word_count=word_limit)
                            full_review += f"{header} {body}\n\n"
                            idx += 1
                    st.session_state.generated_review = full_review

                if st.session_state.generated_review:
                    st.markdown(f'<div class="lit-review-box">{st.session_state.generated_review}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Download Report", st.session_state.generated_review, file_name="Zaid_Research_Report.txt")

# --- TAB 2: CITATION GENERATOR ---
with tab_citations:
    st.subheader("📋 Academic Bibliography Reference List")
    if not st.session_state.selected_ids:
        st.warning("No papers selected. Go to the Research Engine and select papers.")
    else:
        for i, p_id in enumerate(st.session_state.selected_ids):
            p = next(item for item in st.session_state.papers if item["id"] == p_id)
            st.markdown('<div class="citation-item">', unsafe_allow_html=True)
            if style_choice == "IEEE":
                # IEEE Bibliography Style
                ref = f"[{i+1}] {p['authors']}, \"{p['title']}\", arXiv preprint arXiv:{p['id']}, 2026."
            else:
                # Harvard Bibliography Style
                ref = f"{p['authors'].split(',')[0]} ({p.get('year', '2026')}). {p['title']}. Available at: https://arxiv.org/abs/{p['id']}"
            st.code(ref, language="text")
            st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 6. FOOTER
# ----------------------------------------------------------------
st.markdown("---")
st.caption(f"Built by Muhammad Zaid Suhail | Applied AI Engineer | {datetime.now().year}")
