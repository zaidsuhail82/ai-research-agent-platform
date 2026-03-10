import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import base64
from datetime import datetime

# Import your custom modules
try:
    from data_pipeline.paper_ingestion import fetch_papers
    from data_pipeline.document_processor import chunk_text
    from rag.embeddings import embed_text
    from rag.vector_store import add_embedding, search_embedding
    from agents.summarizer_agent import summarize_chunks, generate_lit_review
except ImportError as e:
    st.error(f"Module Import Error: {e}. Please ensure folder structure is correct.")

# ----------------------------------------------------------------
# 1. ANALYTICS & STATE MANAGEMENT (SENIOR ARCHITECTURE)
# ----------------------------------------------------------------
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'selected_papers' not in st.session_state:
    st.session_state.selected_papers = {}
if 'review_data' not in st.session_state:
    st.session_state.review_data = None
if 'global_report' not in st.session_state:
    st.session_state.global_report = None

# ----------------------------------------------------------------
# 2. PAGE CONFIGURATION
# ----------------------------------------------------------------
st.set_page_config(
    page_title="AI Research Agent | Muhammad Zaid Suhail",
    page_icon="logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------------------
# 3. ADVANCED CSS (GOOGLE/MICROSOFT DESIGN SYSTEM)
# ----------------------------------------------------------------
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;600;700&family=Inter:wght@300;400;500;700&family=JetBrains+Mono&display=swap');
    
    :root {
        --primary-blue: #58a6ff;
        --neon-cyan: #00f2fe;
        --dark-bg: #0d1117;
        --card-bg: rgba(22, 27, 34, 0.8);
        --border-color: rgba(255, 255, 255, 0.1);
    }

    /* Global Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: var(--dark-bg); }
    ::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }

    html, body, [data-testid="stWebview"] {
        background: radial-gradient(circle at top right, #161b22, #0d1117);
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
    }

    /* Main Container Padding */
    .main .block-container {
        padding-top: 2rem;
        max-width: 1200px;
    }

    /* Hero Styling */
    .hero-container {
        text-align: center;
        padding: 3rem 0;
        background: rgba(255, 255, 255, 0.02);
        border-radius: 20px;
        border: 1px solid var(--border-color);
        margin-bottom: 2rem;
        backdrop-filter: blur(10px);
    }
    .hero-title {
        font-family: 'SF Pro Display', sans-serif;
        font-size: 3.5rem !important;
        font-weight: 800;
        letter-spacing: -1px;
        background: linear-gradient(90deg, #58a6ff, #00f2fe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .engineer-tag {
        font-family: 'JetBrains Mono', monospace;
        color: var(--primary-blue);
        font-size: 1rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Tab Design */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        justify-content: center;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none !important;
        color: #8b949e !important;
        font-weight: 600 !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--neon-cyan) !important;
        border-bottom: 2px solid var(--neon-cyan) !important;
    }

    /* Glass Cards */
    .glass-card {
        background: var(--card-bg);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        transition: transform 0.2s ease;
    }
    
    /* Result Display */
    .result-box {
        background: rgba(0, 0, 0, 0.2);
        border-left: 4px solid var(--neon-cyan);
        padding: 25px;
        border-radius: 4px 12px 12px 4px;
        font-size: 1.05rem;
        line-height: 1.8;
        color: #e6edf3;
    }

    /* Inputs & Buttons */
    .stButton > button {
        width: 100% !important;
        background: linear-gradient(135deg, #1f6feb, #094cb3) !important;
        color: white !important;
        border: none !important;
        height: 45px !important;
        font-weight: 700 !important;
        border-radius: 8px !important;
        transition: all 0.3s ease !important;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(31, 111, 235, 0.4);
    }
    
    /* Small UI Overrides */
    div[data-testid="stExpander"] {
        background: transparent !important;
        border: 1px solid var(--border-color) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# ----------------------------------------------------------------
# 4. UTILITY FUNCTIONS (ENGINEERED FOR PRECISION)
# ----------------------------------------------------------------
def format_author_citation(authors_str):
    """Converts 'Name Surname' to 'Surname, N. et al.'"""
    try:
        authors = [a.strip() for a in authors_str.split(',')]
        first_author = authors[0]
        parts = first_author.split(' ')
        last_name = parts[-1]
        initial = parts[0][0]
        suffix = " et al." if len(authors) > 1 else ""
        return f"{last_name}, {initial}.{suffix}"
    except:
        return "Unknown Researcher"

def get_arxiv_metadata(url):
    try:
        paper_id = url.split('/')[-1].replace('.pdf', '')
        api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        response = requests.get(api_url, timeout=10)
        root = ET.fromstring(response.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is None: return None
        return {
            "title": entry.find('atom:title', ns).text.strip().replace('\n', ' '),
            "authors": ", ".join([auth.find('atom:name', ns).text for auth in entry.findall('atom:author', ns)]),
            "year": entry.find('atom:published', ns).text[:4],
            "summary": entry.find('atom:summary', ns).text.strip(),
            "id": paper_id
        }
    except:
        return None

# ----------------------------------------------------------------
# 5. HEADER & BRANDING (YOUR IDENTITY)
# ----------------------------------------------------------------
st.markdown('<div class="hero-container">', unsafe_allow_html=True)
if os.path.exists("logo.png"):
    # Center logo using columns for better control
    _, col_img, _ = st.columns([1, 1, 1])
    with col_img:
        st.image("logo.png", width=300)
else:
    st.markdown('<h1 class="hero-title">AI Research Agent</h1>', unsafe_allow_html=True)

st.markdown(f"""
    <div class="hero-title">AI RESEARCH AGENT</div>
    <div class="engineer-tag">Applied AI Engineer & Electrical Engineer</div>
    <p style="color: #8b949e; font-size: 1.2rem; margin-top: 15px;">
        High-Performance Scientific Discovery Platform | <b>Engineered by Muhammad Zaid Suhail</b>
    </p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------------------
# 6. TOOL NAVIGATION (TAB SYSTEM)
# ----------------------------------------------------------------
tab_global, tab_lit = st.tabs(["🌐 GLOBAL DISCOVERY ENGINE", "🔖 ACADEMIC LIT REVIEW"])

# --- TAB 1: GLOBAL RESEARCH ---
with tab_global:
    st.markdown("### 🔍 Semantic Search & Synthesis")
    
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        c_q, c_n, c_b = st.columns([5, 1, 2])
        with c_q:
            keyword_query = st.text_input("Scientific Keywords / Topic", placeholder="e.g. Transformers in Power Systems")
        with c_n:
            paper_count = st.number_input("Limit", 1, 10, 5)
        with c_b:
            st.write(" ") # Padding
            if st.button("🚀 Execute Global Search"):
                if keyword_query:
                    with st.status("🛠️ AI Agents Coordinating...", expanded=True) as status:
                        st.write("📡 Accessing arXiv Open Research API...")
                        papers = fetch_papers(keyword_query, max_results=paper_count)
                        st.session_state.search_results = papers
                        status.update(label="Search Complete", state="complete")
                else:
                    st.warning("Please enter a research topic.")
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.search_results:
        st.markdown(f"#### 📚 Discovery Results ({len(st.session_state.search_results)} Papers found)")
        
        # Displaying Results with Sequential Selection
        for i, paper in enumerate(st.session_state.search_results):
            with st.container():
                st.markdown('<div class="glass-card">', unsafe_allow_html=True)
                col_info, col_sel = st.columns([7, 1])
                
                with col_info:
                    st.markdown(f"**{paper['title']}**")
                    st.caption(f"Authors: {paper.get('authors', 'N/A')} | [View Original Paper](https://arxiv.org/abs/{paper.get('id', '')})")
                    with st.expander("Show Abstract"):
                        st.write(paper['summary'])
                
                with col_sel:
                    is_selected = st.checkbox("Include", key=f"sel_{i}")
                    if is_selected:
                        st.session_state.selected_papers[i] = paper
                    else:
                        st.session_state.selected_papers.pop(i, None)
                st.markdown('</div>', unsafe_allow_html=True)

        # Multi-Paper Lit Review Section
        if st.session_state.selected_papers:
            st.divider()
            st.markdown("### ✍️ Sequential Multi-Paper Synthesis")
            st.info(f"Ready to synthesize {len(st.session_state.selected_papers)} selected papers.")
            
            c_s, c_w, c_gen = st.columns([2, 2, 2])
            with c_s:
                g_style = st.selectbox("Style", ["IEEE", "Harvard"], key="g_style")
            with c_w:
                g_word = st.selectbox("Words per Paper", [30, 50, 80, 100, 150, 200, 250], index=3, key="g_word")
            with c_gen:
                st.write(" ")
                if st.button("Generate Master Report"):
                    combined_report = ""
                    for pid, pdata in st.session_state.selected_papers.items():
                        with st.spinner(f"Synthesizing: {pdata['title'][:40]}..."):
                            cite_tag = format_author_citation(pdata['authors'])
                            year = pdata.get('year', '2026')
                            body = generate_lit_review(pdata['summary'], style=g_style, word_count=g_word)
                            combined_report += f"{cite_tag} ({year}) investigated {pdata['title']}. {body}\n\n"
                    st.session_state.global_report = combined_report

    if st.session_state.global_report:
        st.markdown('<div class="result-box">', unsafe_allow_html=True)
        st.markdown(st.session_state.global_report)
        st.markdown('</div>', unsafe_allow_html=True)
        st.download_button("📥 Download Master Report", st.session_state.global_report, file_name="Zaid_Research_Report.txt")

# --- TAB 2: SINGLE LIT REVIEW ---
with tab_lit:
    st.markdown("### 🔖 Direct Paper Analysis")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([4, 2, 2])
    with c1: 
        cite_url = st.text_input("Paste arXiv PDF or Abstract URL", placeholder="https://arxiv.org/abs/2301.12345")
    with c2: 
        style = st.selectbox("Citation Style", ["IEEE", "Harvard"], key="single_style")
    with c3: 
        w_count = st.selectbox("Word Count", [30, 50, 80, 100, 150, 200, 250], index=3, key="single_word")

    if st.button("Generate Professional Review"):
        if cite_url:
            with st.spinner("Processing metadata and generating synthesis..."):
                meta = get_arxiv_metadata(cite_url)
                if meta:
                    author_tag = format_author_citation(meta['authors'])
                    raw_review = generate_lit_review(meta['summary'], style=style, word_count=w_count)
                    final_text = f"{author_tag} ({meta['year']}) investigated {meta['title']}. {raw_review}"
                    
                    st.session_state.review_data = {
                        "text": final_text,
                        "title": meta['title'],
                        "latex": f"\\section{{Literature Review}}\n\\textbf{{{meta['title']}}} \\\\ \n{final_text}"
                    }
                else:
                    st.error("Invalid URL. Please ensure it is a valid arXiv link.")
        else:
            st.warning("Please provide a URL.")
    st.markdown('</div>', unsafe_allow_html=True)

    # Persistence of Single Review
    if st.session_state.review_data:
        data = st.session_state.review_data
        st.markdown(f"#### Synthesis for: {data['title']}")
        st.markdown(f'<div class="result-box">{data["text"]}</div>', unsafe_allow_html=True)
        
        col_down1, col_down2 = st.columns(2)
        with col_down1:
            st.download_button("📥 Download as .txt", data["text"], file_name="lit_review.txt")
        with col_down2:
            with st.expander("View LaTeX Source"):
                st.code(data["latex"], language="latex")

# ----------------------------------------------------------------
# 7. FOOTER
# ----------------------------------------------------------------
st.divider()
st.markdown(f"""
    <div style="text-align: center; color: #8b949e; padding: 20px;">
        AI Research Agent v3.0 | <span style="color: var(--neon-cyan);">Senior Engineering Project</span><br>
        Developed by <b>Muhammad Zaid Suhail</b> | {datetime.now().year}
    </div>
""", unsafe_allow_html=True)
