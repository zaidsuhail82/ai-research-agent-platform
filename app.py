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
# 1. PAGE CONFIG & STATE
# -------------------------
st.set_page_config(
    page_title="AI Research Agent | Zaid Suhail",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize Session State to prevent "hiding" bug
if 'review_data' not in st.session_state:
    st.session_state.review_data = None
if 'report_data' not in st.session_state:
    st.session_state.report_data = None

# -------------------------
# 2. MICROSOFT/GOOGLE STYLE CSS
# -------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600&family=Inter:wght@300;400;700&display=swap');
    
    :root {
        --glass-bg: rgba(22, 27, 34, 0.7);
        --accent-glow: 0 0 20px rgba(88, 166, 255, 0.3);
    }

    html, body, [data-testid="stWebview"] {
        background: radial-gradient(circle at top right, #161b22, #0d1117);
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }

    /* Glassmorphism Containers */
    .stContainer, .tool-card {
        background: var(--glass-bg);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 20px;
        box-shadow: var(--accent-glow);
    }

    /* Hero Section */
    .hero-container {
        text-align: center;
        padding: 2rem 0;
        margin-bottom: 2rem;
    }
    .hero-title {
        font-family: 'SF Pro Display', sans-serif;
        font-size: 3rem !important;
        font-weight: 700;
        background: linear-gradient(90deg, #58a6ff, #00bcd4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    .hero-subtitle {
        color: #8b949e;
        font-size: 1.1rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    /* Premium Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #1f6feb, #094cb3) !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(31, 111, 235, 0.4);
    }

    /* Compact Inputs */
    input { font-size: 0.9rem !important; }
    
    /* Result Box */
    .result-area {
        background: #0d1117;
        border-left: 4px solid #58a6ff;
        padding: 20px;
        border-radius: 0 8px 8px 0;
        font-size: 1rem;
        line-height: 1.7;
        margin-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# -------------------------
# 3. SENIOR ENGINEER LOGIC (Author Parsing)
# -------------------------
def format_academic_citation(meta):
    """Formats: 'Last Name, F. et al.' as requested."""
    try:
        authors = meta['authors'].split(',')
        first_author = authors[0].strip()
        last_name = first_author.split(' ')[-1]
        initial = first_author[0]
        
        et_al = " et al." if len(authors) > 1 else ""
        return f"{last_name}, {initial}.{et_al}"
    except:
        return "The researchers"

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
# 4. BRANDING & HERO
# -------------------------
st.markdown('<div class="hero-container">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    st.image("logo.png", width=350)
else:
    st.markdown('<h1 class="hero-title">AI Research Agent</h1>', unsafe_allow_html=True)

st.markdown(f"""
    <div class="hero-subtitle">Advanced Scientific Discovery Platform</div>
    <p style="color: #c9d1d9; margin-top: 10px;">
        <b>Engineered by:</b> Muhammad Zaid Suhail <br>
        <span style="color: #58a6ff; font-size: 0.85rem;">Applied AI Engineer | Electrical Engineer</span>
    </p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# 5. TOOLS (Tabs for Google-like feel)
# -------------------------
tab_lit, tab_global = st.tabs(["🔖 Literature Review", "🌐 Global Research"])

with tab_lit:
    c1, c2, c3 = st.columns([4, 2, 2])
    with c1: cite_url = st.text_input("arXiv Paper URL", placeholder="https://arxiv.org/abs/...")
    with c2: style = st.selectbox("Style", ["IEEE", "Harvard"])
    with c3: w_count = st.selectbox("Word Count", [30, 50, 80, 100, 150, 200, 250], index=3)

    if st.button("Generate Senior-Level Review"):
        with st.spinner("Synthesizing research..."):
            meta = get_arxiv_metadata(cite_url)
            if meta:
                author_tag = format_academic_citation(meta)
                # Call agent
                raw_review = generate_lit_review(meta['summary'], style=style, word_count=w_count)
                
                # Format with requested "Last Name, F." style
                final_review = f"{author_tag} ({meta['year']}) investigated {meta['title']}. {raw_review}"
                
                # SAVE TO STATE to prevent disappearing
                st.session_state.review_data = {
                    "text": final_review,
                    "meta": meta,
                    "latex": f"\\section{{Literature Review}}\n{final_review}"
                }
            else:
                st.error("Could not fetch paper metadata.")

    # DISPLAY AREA (Checks state)
    if st.session_state.review_data:
        data = st.session_state.review_data
        st.markdown(f'<div class="result-area">{data["text"]}</div>', unsafe_allow_html=True)
        
        # Download Buttons (Standard st.download_button DOES NOT refresh the page)
        col_a, col_b = st.columns(2)
        with col_a:
            st.download_button("📥 Download Review (.txt)", data["text"], file_name="review.txt")
        with col_b:
            with st.expander("View LaTeX Source"):
                st.code(data["latex"], language="latex")

with tab_global:
    # (Existing Global Research code goes here, use the same st.session_state logic)
    st.info("Global Research Agent Platform Active.")
