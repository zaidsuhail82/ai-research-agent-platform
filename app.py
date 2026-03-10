import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import pandas as pd
import random
from datetime import datetime
import collections
import re

# ----------------------------------------------------------------
# 1. CORE ENGINE & STATE INITIALIZATION
# ----------------------------------------------------------------
# Using a robust dictionary-based state to prevent "KeyError"
if 'research_state' not in st.session_state:
    st.session_state.research_state = {
        'search_results': [],
        'selected_indices': set(),
        'master_report': "",
        'bibtex_log': "",
        'search_query': ""
    }

# ----------------------------------------------------------------
# 2. DESIGN SYSTEM & UI OVERRIDES
# ----------------------------------------------------------------
st.set_page_config(
    page_title="AI Research Agent | Muhammad Zaid Suhail",
    page_icon="media/logo.png",
    layout="wide"
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=JetBrains+Mono&display=swap');
    
    :root {
        --glow: #00f2fe;
        --bg: #0d1117;
        --card: rgba(22, 27, 34, 0.9);
    }

    .stApp { background: var(--bg); color: #c9d1d9; font-family: 'Inter', sans-serif; }
    
    /* Premium Glass Container */
    .phd-container {
        background: var(--card);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 2rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }

    /* Professional Title */
    .hero-text {
        text-align: center;
        background: linear-gradient(90deg, #fff, var(--glow));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0px;
    }
    
    .hero-sub {
        text-align: center;
        color: #8b949e;
        font-family: 'JetBrains Mono';
        letter-spacing: 2px;
        margin-bottom: 2rem;
    }

    /* Scientific Result Box */
    .report-area {
        background: #010409;
        border-left: 4px solid var(--glow);
        padding: 30px;
        border-radius: 8px;
        line-height: 1.8;
        font-size: 1.1rem;
        color: #e6edf3;
        white-space: pre-wrap;
    }

    /* Buttons */
    .stButton>button {
        width: 100%;
        background: linear-gradient(45deg, #1f6feb, #00f2fe) !important;
        border: none !important;
        color: white !important;
        font-weight: 700 !important;
        height: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------
# 3. SCIENTIFIC AGENT UTILITIES
# ----------------------------------------------------------------

def get_academic_verb():
    return random.choice([
        "investigated", "pioneered", "elucidated", "scrutinized", 
        "analyzed", "proposed", "formulated", "evaluated", "demonstrated"
    ])

def format_citation_logic(paper, style, index):
    """
    IEEE: [index] Author verb ...
    Harvard: Author et al. (Year) verb ...
    """
    authors = paper.get('authors', 'Unknown').split(',')
    first_author = authors[0].strip().split(' ')[-1] # Get Last Name
    year = paper.get('year', '2026')
    verb = get_academic_verb()
    
    if style == "IEEE":
        return f"{first_author} [{index}] {verb}"
    else:
        et_al = " et al." if len(authors) > 1 else ""
        return f"{first_author}{et_al} ({year}) {verb}"

def generate_bibtex(paper):
    authors = paper.get('authors', 'Unknown').replace(',', ' and ')
    cite_key = f"{paper.get('authors','auth').split()[0].lower()}{paper.get('id','000')}"
    return f"""@article{{{cite_key},
  title={{{paper['title']}}},
  author={{{authors}}},
  year={{{paper.get('year', '2026')}}},
  journal={{arXiv preprint}},
  eprint={{{paper['id']}}}
}}"""

# ----------------------------------------------------------------
# 4. HEADER & BRANDING
# ----------------------------------------------------------------

logo_path = "media/logo.png" if os.path.exists("media/logo.png") else "logo.png"
col_l, col_c, col_r = st.columns([1, 2, 1])
with col_c:
    if os.path.exists(logo_path):
        st.image(logo_path, width=250)
    st.markdown('<div class="hero-text">AI RESEARCH AGENT</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="hero-sub">MUHAMMAD ZAID SUHAIL | APPLIED AI & ELECTRICAL ENGINEER</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 5. THE FOUR PILLARS (TABS)
# ----------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs(["🌐 DISCOVERY", "🔬 SYNTHESIS", "📊 TRENDS", "📂 LIBRARY"])

# --- TAB 1: DISCOVERY ---
with tab1:
    st.markdown('<div class="phd-container">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([4, 2, 2])
    with c1: 
        q = st.text_input("Enter Research Keywords", placeholder="e.g. Deep Reinforcement Learning for Microgrids")
    with c2:
        cat = st.selectbox("Category", ["cs.AI", "cs.LG", "eess.SY", "math.OC"])
    with c3:
        num = st.number_input("Count", 1, 20, 5)
    
    if st.button("🔍 Execute Search"):
        if q:
            from data_pipeline.paper_ingestion import fetch_papers
            results = fetch_papers(f"{q} cat:{cat}", max_results=num)
            st.session_state.research_state['search_results'] = results
            st.session_state.research_state['selected_indices'] = set() # Reset selection
        else: st.error("Search query is empty.")
    st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.research_state['search_results']:
        st.write("### Search Results")
        for i, p in enumerate(st.session_state.research_state['search_results']):
            with st.expander(f"📄 {p['title']}"):
                st.write(p['summary'])
                st.caption(f"ID: {p['id']} | Authors: {p['authors']}")
                
                # Checkbox to add to global state
                if st.checkbox("Include in Synthesis", key=f"sel_{i}_{p['id']}"):
                    st.session_state.research_state['selected_indices'].add(i)
                else:
                    st.session_state.research_state['selected_indices'].discard(i)

# --- TAB 2: SYNTHESIS (FIXED) ---
with tab2:
    selected_indices = st.session_state.research_state['selected_indices']
    if not selected_indices:
        st.warning("No papers selected. Go to Discovery tab and check 'Include in Synthesis'.")
    else:
        st.markdown('<div class="phd-container">', unsafe_allow_html=True)
        col_st, col_wc = st.columns(2)
        with col_st: style = st.selectbox("Style", ["IEEE", "Harvard"])
        with col_wc: w_count = st.select_slider("Word Count per Paper", [50, 100, 150, 200, 250], value=100)
        
        if st.button("✍️ Generate Literature Review"):
            from agents.summarizer_agent import generate_lit_review
            full_text = ""
            for idx, paper_idx in enumerate(selected_indices):
                paper = st.session_state.research_state['search_results'][paper_idx]
                with st.spinner(f"Synthesizing Paper {idx+1}..."):
                    cite_head = format_citation_logic(paper, style, idx+1)
                    body = generate_lit_review(paper['summary'], style=style, word_count=w_count)
                    full_text += f"{cite_head} {body}\n\n"
            st.session_state.research_state['master_report'] = full_text
        st.markdown('</div>', unsafe_allow_html=True)

        if st.session_state.research_state['master_report']:
            st.markdown("### Generated Synthesis")
            st.markdown(f'<div class="report-area">{st.session_state.research_state["master_report"]}</div>', unsafe_allow_html=True)
            st.download_button("Download Report (.txt)", st.session_state.research_state['master_report'])

# --- TAB 3: TRENDS (FIXED LOGIC) ---
with tab3:
    st.write("### 📊 NLP Intelligence")
    results = st.session_state.research_state['search_results']
    if not results:
        st.info("Run a search to see trend analysis.")
    else:
        all_summaries = " ".join([p['summary'] for p in results]).lower()
        # Simple Frequency Analysis for Senior Tooling
        words = re.findall(r'\w+', all_summaries)
        stop_words = {'the', 'a', 'in', 'of', 'and', 'to', 'for', 'with', 'on', 'is', 'by', 'this'}
        filtered_words = [w for w in words if w not in stop_words and len(w) > 4]
        counts = collections.Counter(filtered_words).most_common(10)
        
        st.markdown('<div class="phd-container">', unsafe_allow_html=True)
        st.write("**Top Keywords in Current Research Field:**")
        df_trends = pd.DataFrame(counts, columns=['Keyword', 'Frequency'])
        st.bar_chart(df_trends.set_index('Keyword'))
        st.markdown('</div>', unsafe_allow_html=True)

# --- TAB 4: LIBRARY (FIXED BIBTEX) ---
with tab4:
    st.write("### 📂 BibTeX Library")
    indices = st.session_state.research_state['selected_indices']
    if not indices:
        st.info("Select papers to generate BibTeX entries.")
    else:
        bib_output = ""
        for i in indices:
            paper = st.session_state.research_state['search_results'][i]
            bib_output += generate_bibtex(paper) + "\n\n"
        
        st.markdown('<div class="phd-container">', unsafe_allow_html=True)
        st.code(bib_output, language="latex")
        st.download_button("Download .bib File", bib_output, file_name="zaid_references.bib")
        st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 6. FOOTER
# ----------------------------------------------------------------
st.divider()
st.caption(f"Developed by Muhammad Zaid Suhail | AI Research Agent v4.0 | © {datetime.now().year}")
