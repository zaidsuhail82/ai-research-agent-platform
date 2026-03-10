import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
from data_pipeline.paper_ingestion import fetch_papers
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks, generate_lit_review

# -------------------------
# 1. PAGE CONFIGURATION
# -------------------------
st.set_page_config(
    page_title="Zaid AI | Research Platform",
    page_icon="image_9.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------
# 2. COMPACT SENIOR CSS
# -------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
    
    html, body, [data-testid="stWebview"] {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }

    /* Reduce spacing everywhere */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; max-width: 1100px !important; }
    
    /* Branding */
    .brand-text { text-align: center; margin-bottom: 10px; }
    .branding-subtitle { color: #8b949e; font-size: 0.9rem; margin-top: -5px; }
    .branding-name { color: #58a6ff; font-weight: 700; }

    /* Compact Buttons */
    .stButton > button {
        height: 28px !important;
        padding: 0px 15px !important;
        font-size: 0.85rem !important;
        border-radius: 4px !important;
        background-color: #21262d !important;
        border: 1px solid #30363d !important;
        color: #c9d1d9 !important;
    }
    
    /* Highlight Action Buttons */
    button[data-testid*="Execute"], button[data-testid*="Generate"] {
        background-color: #238636 !important; /* GitHub Green */
        color: white !important;
        border: none !important;
    }

    /* Small Input Boxes */
    div[data-testid="stTextInput"] input, .stSelectbox div {
        background-color: #0d1117 !important;
        font-size: 0.85rem !important;
        height: 30px !important;
    }

    /* Custom Report Box */
    .report-box {
        padding: 10px;
        border-radius: 6px;
        background-color: #161b22;
        border: 1px solid #30363d;
        font-size: 0.9rem;
        line-height: 1.4;
        margin-top: 5px;
    }

    /* Small Radio Menu */
    div[data-testid="stHorizontalBlock"] { gap: 0.5rem !important; }
    .stRadio div[role="radiogroup"] { gap: 10px; }

    hr { margin: 10px 0 !important; border-color: #30363d; }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# 3. HELPER FUNCTIONS
# -------------------------
def get_arxiv_metadata(url):
    try:
        paper_id = url.split('/')[-1].replace('.pdf', '')
        api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        response = requests.get(api_url)
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is None: return None
        return {
            "title": entry.find('atom:title', ns).text.strip().replace('\n', ' '),
            "authors": ", ".join([auth.find('atom:name', ns).text for auth in entry.findall('atom:author', ns)]),
            "year": entry.find('atom:published', ns).text[:4],
            "summary": entry.find('atom:summary', ns).text.strip()
        }
    except: return None

# -------------------------
# 4. COMPACT BRANDING
# -------------------------
st.markdown('<div class="brand-text">', unsafe_allow_html=True)
if os.path.exists("image_9.png"):
    st.image("image_9.png", width=450) # Smaller centered logo
else:
    st.subheader("SYNTHETIC LOOP AI")
st.markdown('<p class="branding-subtitle">Research Intelligence | <span class="branding-name">M. Zaid Suhail</span></p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- THE MENU (Functional) ---
tool = st.radio("", ["Global Research Agent", "Literature Review & Citation"], horizontal=True, label_visibility="collapsed")
st.markdown("<hr>", unsafe_allow_html=True)

# -------------------------
# 5. TOOL IMPLEMENTATION
# -------------------------

if tool == "Literature Review & Citation":
    col1, col2, col3 = st.columns([4, 2, 2])
    with col1:
        cite_url = st.text_input("arXiv URL", placeholder="Paste link here...", label_visibility="collapsed")
    with col2:
        style = st.selectbox("Style", ["IEEE", "Harvard"], label_visibility="collapsed")
    with col3:
        w_count = st.selectbox("Words", [30, 50, 80, 100, 150, 200, 250], index=3, label_visibility="collapsed")

    if cite_url:
        meta = get_arxiv_metadata(cite_url)
        if meta:
            # Citations
            ieee = f"{meta['authors']}, \"{meta['title']},\" arXiv, {meta['year']}."
            st.code(ieee, language=None)
            
            if st.button("Generate Literature Review"):
                with st.spinner("Processing..."):
                    review = generate_lit_review(meta['summary'], style=style, word_count=w_count)
                    st.markdown(f'<div class="report-box">{review}</div>', unsafe_allow_html=True)
                    
                    # Small utility buttons
                    c1, c2 = st.columns(2)
                    with c1: st.button("Copy LaTeX")
                    with c2: st.button("Download Docx")
        else:
            st.error("Paper not found.")

else: # Global Research
    c1, c2, c3 = st.columns([5, 1, 1])
    with c1:
        query = st.text_input("Topic", placeholder="Search papers...", label_visibility="collapsed")
    with c2:
        num = st.number_input("Count", 1, 10, 5, label_visibility="collapsed")
    with c3:
        execute = st.button("Execute")

    if execute and query:
        with st.status("Analyzing...", expanded=False):
            papers = fetch_papers(query=query, max_results=num)
            for p in papers:
                chunks = chunk_text(p["summary"], chunk_size=500)
                for c in chunks:
                    add_embedding(embed_text(c), {"title": p["title"], "chunk": c})
            
            results = search_embedding(embed_text(query), k=5)
            report = summarize_chunks(results)
        
        st.markdown(f'<div class="report-box"><b>Synthesis:</b><br>{report}</div>', unsafe_allow_html=True)

