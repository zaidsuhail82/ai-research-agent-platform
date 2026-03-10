import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from io import BytesIO
from docx import Document
import base64

# -------------------------------
# Custom Modules (Summarizer)
# -------------------------------
try:
    from agents.summarizer_agent import generate_lit_review
except ImportError:
    st.error("Summarizer agent not found. Ensure agents/summarizer_agent.py exists")

# -------------------------------
# Page Config
# -------------------------------
st.set_page_config(
    page_title="AI Research Agent | Muhammad Zaid Suhail",
    page_icon="media/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------
# Advanced CSS
# -------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
:root{
--primary-blue: #58a6ff;
--neon-cyan: #00f2fe;
--dark-bg: #0d1117;
--card-bg: rgba(22,27,34,0.8);
--border-color: rgba(255,255,255,0.1);
}
html, body, [data-testid="stWebview"] {
    background: radial-gradient(circle at top right, #161b22, #0d1117);
    color:#c9d1d9;
    font-family: 'Inter', sans-serif;
}
.hero-container{
    text-align:center;
    padding:2rem;
    border-radius:20px;
    background:rgba(255,255,255,0.02);
    border:1px solid var(--border-color);
    margin-bottom:2rem;
    backdrop-filter: blur(10px);
}
.hero-title{
    font-size:3rem !important;
    font-weight:800;
    background: linear-gradient(90deg, #58a6ff, #00f2fe);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.engineer-tag{color: var(--primary-blue); font-weight:500; letter-spacing:2px;}
.glass-card{
    background: var(--card-bg);
    border:1px solid var(--border-color);
    border-radius:12px;
    padding:20px;
    margin-bottom:20px;
}
.result-box{
    background: rgba(0,0,0,0.2);
    border-left: 4px solid var(--neon-cyan);
    padding:20px;
    border-radius:4px 12px 12px 4px;
    font-size:1rem;
    line-height:1.6;
}
.stButton>button{
    width:100% !important;
    background: linear-gradient(135deg,#1f6feb,#094cb3) !important;
    color:white !important;
    border:none !important;
    height:45px !important;
    font-weight:700 !important;
    border-radius:8px !important;
}
.stButton>button:hover{
    transform: translateY(-2px);
    box-shadow:0 4px 20px rgba(31,111,235,0.4);
}
</style>
""", unsafe_allow_html=True)

# -------------------------------
# Header / Hero
# -------------------------------
st.markdown('<div class="hero-container">', unsafe_allow_html=True)
if os.path.exists("media/logo.png"):
    _, c_img, _ = st.columns([1,1,1])
    with c_img:
        st.image("media/logo.png", width=250)
else:
    st.markdown('<h1 class="hero-title">AI Research Agent</h1>', unsafe_allow_html=True)

st.markdown("""
<div class="hero-title">AI RESEARCH AGENT</div>
<div class="engineer-tag">Applied AI Engineer & Electrical Engineer</div>
<p style="color:#8b949e; margin-top:10px;">High-Performance Scientific Discovery Platform | <b>By Muhammad Zaid Suhail</b></p>
""", unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# Tabs: Citation & Lit Review
# -------------------------------
tab1, tab2 = st.tabs(["🔖 Citation Generator", "✍️ Literature Review Writer"])

# ---------------------------------------
# Helper Functions
# ---------------------------------------
def get_arxiv_metadata(url):
    """Fetch metadata from arXiv"""
    try:
        paper_id = url.split("/")[-1].replace(".pdf","")
        api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        resp = requests.get(api_url, timeout=10)
        root = ET.fromstring(resp.content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', ns)
        if entry is None: return None
        return {
            "title": entry.find('atom:title', ns).text.strip().replace('\n',' '),
            "authors": [a.find('atom:name',ns).text for a in entry.findall('atom:author', ns)],
            "year": entry.find('atom:published', ns).text[:4],
            "summary": entry.find('atom:summary', ns).text.strip()
        }
    except:
        return None

def format_citation(authors, style="Harvard"):
    """Return first author with et al. if needed"""
    try:
        first = authors[0]
        last = first.split()[-1]
        initial = first[0]
        suffix = " et al." if len(authors) > 1 else ""
        if style.lower()=="ieee":
            suffix = "" # IEEE no et al.
        return f"{last}, {initial}.{suffix}"
    except:
        return "Unknown"

def download_txt(content, filename="review.txt"):
    b = content.encode()
    st.download_button("📥 Download TXT", b, file_name=filename, key=f"{filename}_txt")

def download_docx(content, filename="review.docx"):
    doc = Document()
    doc.add_paragraph(content)
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    st.download_button("📥 Download DOCX", buf, file_name=filename, key=f"{filename}_docx")

def generate_first_line():
    """Return varied first line synonyms"""
    options = [
        "examined", "analyzed", "investigated", "explored", "evaluated", "studied", "assessed"
    ]
    import random
    return random.choice(options)

# -------------------------------
# Tab1: Citation Generator
# -------------------------------
with tab1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    arxiv_url = st.text_input("Paste arXiv URL", placeholder="https://arxiv.org/abs/xxxx.xxxxx", key="cite_url")
    style = st.selectbox("Citation Style", ["Harvard","IEEE"], key="cite_style")
    if st.button("Generate Citation", key="gen_citation_btn"):
        if arxiv_url:
            meta = get_arxiv_metadata(arxiv_url)
            if meta:
                citation_text = format_citation(meta["authors"], style) + f", \"{meta['title']}\", arXiv, {meta['year']}."
                st.markdown(f'<div class="result-box">{citation_text}</div>', unsafe_allow_html=True)
                download_txt(citation_text,"citation.txt")
                download_docx(citation_text,"citation.docx")
            else:
                st.error("Could not fetch paper metadata.")
        else:
            st.warning("Enter a valid arXiv URL.")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# Tab2: Literature Review Writer
# -------------------------------
with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    arxiv_url2 = st.text_input("Paste arXiv URL", placeholder="https://arxiv.org/abs/xxxx.xxxxx", key="lit_url")
    style2 = st.selectbox("Citation Style", ["Harvard","IEEE"], key="lit_style")
    word_count = st.selectbox("Word Count", [30,50,80,100,150,200,250], index=3, key="lit_words")
    if st.button("Generate Literature Review", key="gen_lit_btn"):
        if arxiv_url2:
            meta2 = get_arxiv_metadata(arxiv_url2)
            if meta2:
                first_line_verb = generate_first_line()
                author_tag = format_citation(meta2["authors"], style2)
                lit_review = generate_lit_review(meta2["summary"], style=style2, word_count=word_count)
                final_text = f"{author_tag} ({meta2['year']}) {first_line_verb} {meta2['title']}. {lit_review}"
                st.markdown(f'<div class="result-box">{final_text}</div>', unsafe_allow_html=True)
                download_txt(final_text,"literature_review.txt")
                download_docx(final_text,"literature_review.docx")
                latex_code = f"\\section{{Literature Review}}\n\\textbf{{{meta2['title']}}}\\\\\n{final_text}"
                with st.expander("View LaTeX Source"):
                    st.code(latex_code, language="latex")
            else:
                st.error("Invalid arXiv URL.")
        else:
            st.warning("Enter a valid arXiv URL.")
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------------
# Footer
# -------------------------------
st.divider()
st.markdown(f"""
<div style="text-align:center; color:#8b949e; padding:20px;">
AI Research Agent v3.0 | <span style="color:var(--neon-cyan);">Professional Literature Platform</span><br>
Developed by <b>Muhammad Zaid Suhail</b> | {datetime.now().year}
</div>
""", unsafe_allow_html=True)
