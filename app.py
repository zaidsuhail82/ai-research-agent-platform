import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
# Assuming these imports are correct based on your file structure
from data_pipeline.paper_ingestion import fetch_papers, get_paper_content
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks, generate_lit_review

# -------------------------
# 1. PAGE CONFIGURATION
# -------------------------
st.set_page_config(
    page_title="Zaid AI | Research Platform",
    page_icon="image_9.png", # Using the provided image as the page icon
    layout="wide",
    initial_sidebar_state="collapsed" # Hide sidebar by default
)

# -------------------------
# 2. CUSTOM CSS (Senior AI Level Theme)
# -------------------------
st.markdown("""
    <style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [data-testid="stWebview"] {
        font-family: 'Inter', sans-serif;
        background-color: #0d1117; /* Dark GitHub-like background */
        color: #c9d1d9;
    }
    
    /* Main Content Area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px; /* Center and constrain width */
        margin: auto;
    }

    /* Header Styling */
    .header-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        margin-bottom: 3rem;
        padding-bottom: 2rem;
        border-bottom: 1px solid #21262d;
    }
    .main-logo {
        margin-bottom: 1rem;
    }
    .stTitle {
        font-weight: 700;
        color: #f0f6fc;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem;
    }
    .branding-subtitle {
        color: #8b949e;
        font-size: 1.1rem;
        margin-bottom: 1.5rem;
    }
    .branding-name {
        color: #58a6ff; /* Microsoft/Google Blue */
        font-size: 1.3rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }

    /* Tool Selection Area */
    .tool-selector-container {
        display: flex;
        justify-content: space-around;
        margin-bottom: 2rem;
        padding: 1rem;
        background-color: #161b22;
        border-radius: 12px;
        border: 1px solid #30363d;
    }

    /* Tool Container Styling */
    .tool-container {
        background-color: #161b22;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #30363d;
        margin-bottom: 1.5rem;
    }
    .tool-header {
        font-weight: 600;
        color: #f0f6fc;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        display: flex;
        align-items: center;
    }
    .tool-icon {
        margin-right: 0.5rem;
        color: #58a6ff;
    }

    /* Input & Select Styling */
    div[data-testid="stTextInput"] > div > div > input,
    div[data-testid="stSelectbox"] > div > div > div {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        border-color: #30363d !important;
    }

    /* Button Styling */
    .stButton > button {
        width: auto; /* Smaller buttons */
        padding: 0.5rem 1.5rem;
        border-radius: 6px;
        font-weight: 600;
        border: none;
        transition: background-color 0.2s;
    }
    
    /* Action Buttons (Cyan) */
    .stButton > button[data-testid="stButton-Execute Autonomous Research"],
    .stButton > button[data-testid="stButton-Extract Citation"],
    .stButton > button[data-testid="stButton-Generate Literature Review"] {
        background-color: #00bcd4;
        color: #0d1117;
    }
    .stButton > button[data-testid="stButton-Execute Autonomous Research"]:hover,
    .stButton > button[data-testid="stButton-Extract Citation"]:hover,
    .stButton > button[data-testid="stButton-Generate Literature Review"]:hover {
        background-color: #00acc1;
    }

    /* Sub-Action Buttons (Blue) */
    .stButton > button[data-testid="stButton-Copy"],
    .stButton > button[data-testid="stButton-Download (.docx)"] {
        background-color: #1f6feb;
        color: white;
    }
    .stButton > button[data-testid="stButton-Copy"]:hover,
    .stButton > button[data-testid="stButton-Download (.docx)"]:hover {
        background-color: #388bfd;
    }

    /* Code Block (LaTeX) styling */
    .stCode > div {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
    }

    /* Report Box */
    .report-box {
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 5px solid #00bcd4;
        color: #c9d1d9;
        font-family: 'Inter', sans-serif;
        font-size: 1rem;
        line-height: 1.6;
        margin-top: 1rem;
        min-height: 50px;
        max-height: 400px;
        overflow-y: auto;
    }

    /* Expander Styling */
    div[data-testid="stExpander"] {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    div[data-testid="stExpander"] > details > summary {
        color: #f0f6fc !important;
    }

    /* Citation Card */
    .citation-card {
        padding: 1rem;
        background-color: #1c2128;
        border-radius: 8px;
        border: 1px solid #30363d;
        margin-bottom: 0.5rem;
        color: #c9d1d9;
    }

    </style>
    """, unsafe_allow_html=True)

# -------------------------
# 3. HELPER FUNCTIONS
# -------------------------
def get_arxiv_metadata(url):
    try:
        # Clean the URL to get the ID
        paper_id = url.split('/')[-1].replace('.pdf', '')
        api_url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        response = requests.get(api_url)
        root = ET.fromstring(response.content)
        
        namespace = {'atom': 'http://www.w3.org/2005/Atom'}
        entry = root.find('atom:entry', namespace)
        
        if entry is None: return None
        
        title = entry.find('atom:title', namespace).text.strip().replace('\n', ' ')
        published = entry.find('atom:published', namespace).text[:4]
        
        authors = [auth.find('atom:name', namespace).text for auth in entry.findall('atom:author', namespace)]
        author_str = ", ".join(authors)
        
        return {
            "title": title,
            "authors": author_str,
            "year": published
        }
    except Exception:
        return None

# Placeholder function for lit review generation based on style and word count
def generate_proper_lit_review(paper_content, style, word_count):
    # This would involve calling a sophisticated LLM prompt
    # Return a string and the actual word count for now
    review_text = f"This is a proper literature review in {style} style of approximately {word_count} words. It synthesizes key concepts and contributions from the provided paper content... (placeholder text)"
    actual_word_count = len(review_text.split())
    return review_text, actual_word_count

# Placeholder for downloading in docx (would use a library like python-docx)
def download_lit_review_docx(text, filename):
    st.info("Download as DOCX requested. (Logic placeholder)")
    # This would generate and offer a download link for a .docx file

# -------------------------
# 4. SINGLE PAGE MAIN INTERFACE
# -------------------------

# Centered Header with Branding
st.markdown('<div class="header-container">', unsafe_allow_html=True)
if os.path.exists("image_9.png"):
    # Using the banner as logo, constraining height
    st.image("image_9.png", height=100, output_format="PNG", className="main-logo") 
else:
    st.markdown('<div class="main-logo stTitle">SYNTHETIC LOOP AI</div>', unsafe_allow_html=True)

st.title("🔬 Autonomous AI Research Agent")

st.markdown("""
    <div class="branding-subtitle">
        A Persistent Learning Loop for Scientific Discovery | 
        <span class="branding-name">
            Engineered by M. Zaid Suhail
        </span>
    </div>
    """, unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- Tool Selector ---
tool_options = ["Global Research", "Lit Review & Citation"]
selected_tool = st.radio("Select Tool Platform", tool_options, horizontal=True, label_visibility="collapsed")

# -------------------------
# 5. TOOL IMPLEMENTATION
# -------------------------

if selected_tool == "Lit Review & Citation":
    st.markdown('<div class="tool-container">', unsafe_allow_html=True)
    st.markdown('<div class="tool-header">🔖 Paper Citation & Literature Review</div>', unsafe_allow_html=True)
    
    col_input, col_style, col_count = st.columns([4, 2, 2])
    
    with col_input:
        cite_url = st.text_input("Paste arXiv Paper URL", key="cite_url_input", label_visibility="collapsed")
    
    # --- Citation Extraction ---
    if cite_url:
        meta = get_arxiv_metadata(cite_url)
        if meta:
            ieee_cite = f"{meta['authors']}, \"{meta['title']},\" arXiv preprint, {meta['year']}."
            harvard_cite = f"{meta['authors']} ({meta['year']}) '{meta['title']}', arXiv preprint."
            
            st.markdown('<div class="tool-header">Extract Citation</div>', unsafe_allow_html=True)
            col_ieee, col_harv = st.columns(2)
            
            with col_ieee:
                st.markdown(f"**IEEE:**")
                st.code(ieee_cite, language=None)
                if st.button("Copy IEEE Citation"):
                    st.toast("IEEE Citation Copied to Clipboard!")
                    st.write(f'<script>navigator.clipboard.writeText("{ieee_cite}")</script>', unsafe_allow_html=True)

            with col_harv:
                st.markdown(f"**Harvard:**")
                st.code(harvard_cite, language=None)
                if st.button("Copy Harvard Citation"):
                    st.toast("Harvard Citation Copied to Clipboard!")
                    st.write(f'<script>navigator.clipboard.writeText("{harvard_cite}")</script>', unsafe_allow_html=True)

            # --- Literature Review Generation ---
            st.divider()
            st.markdown('<div class="tool-header">Generate Literature Review</div>', unsafe_allow_html=True)
            
            # Sub-options inside the main tool container
            col_rev_type, col_rev_style, col_rev_count = st.columns(3)
            
            with col_rev_type:
                review_type = st.radio("Review Type", ["Literature Review", "Concise Summary"], horizontal=True)
            
            with col_rev_style:
                review_style = st.selectbox("Citation Style", ["IEEE", "Harvard"])
            
            with col_rev_count:
                word_count_option = st.selectbox("Target Word Count", ["30", "50", "80", "100", "150", "200", "250"], index=3) # Default 100
                word_count = int(word_count_option)

            if st.button("Generate Literature Review"):
                with st.spinner(f"Generating proper {review_style} style literature review..."):
                    # For demo, just pass the metadata, in reality, pass paper content
                    paper_content = f"Title: {meta['title']}, Authors: {meta['authors']}" 
                    review_text, actual_count = generate_proper_lit_review(paper_content, review_style, word_count)
                    
                    if not review_text:
                        st.error("Literature review generation failed.")
                    else:
                        st.session_state['lit_review_text'] = review_text
                        st.session_state['lit_review_count'] = actual_count
                        st.session_state['lit_review_style'] = review_style

            # Output Area for Lit Review
            if 'lit_review_text' in st.session_state:
                st.markdown(f'<div class="report-box">{st.session_state["lit_review_text"]}</div>', unsafe_allow_html=True)
                st.caption(f"Actual Word Count: {st.session_state['lit_review_count']} | Style: {st.session_state['lit_review_style']}")
                
                # Action Buttons for the output
                col_copy, col_latex, col_docx = st.columns(3)
                with col_copy:
                    if st.button("Copy Review"):
                        st.toast("Copied Review Text!")
                        st.write(f'<script>navigator.clipboard.writeText("{st.session_state["lit_review_text"]}")</script>', unsafe_allow_html=True)
                
                with col_latex:
                    # Provide a simple LaTeX wrapper for demo
                    latex_code = f"\\textbf{{Literature Review}} ({st.session_state['lit_review_style']}):\\\\\\indent {st.session_state['lit_review_text']}"
                    with st.expander("Show LaTeX Code"):
                        st.code(latex_code, language="latex")
                
                with col_docx:
                    if st.button("Download Lit Review (.docx)"):
                        download_lit_review_docx(st.session_state['lit_review_text'], "lit_review.docx")

        else:
            st.error("Invalid arXiv URL or metadata not found.")
    st.markdown('</div>', unsafe_allow_html=True)


elif selected_tool == "Global Research":
    st.markdown('<div class="tool-container">', unsafe_allow_html=True)
    st.markdown('<div class="tool-header">🚀 Autonomous Global Research Agent</div>', unsafe_allow_html=True)
    
    # --- RESEARCH SECTION ---
    col_query, col_papers, col_topk = st.columns([5, 1, 1])
    with col_query:
        query = st.text_input("Enter Research Topic", placeholder="e.g., Neural Ordinary Differential Equations")
    with col_papers:
        num_papers = st.number_input("# Papers", value=5, min_value=1, max_value=10)
    with col_topk:
        top_k = st.number_input("Top-K", value=5, min_value=1, max_value=10)

    # Move granular parameters inside autonomous research execution to keep UI clean
    with st.expander("Search Parameters", expanded=False):
        c_size = st.select_slider("Chunk Granularity", options=[300, 500, 800, 1200], value=500)

    if st.button("Execute Autonomous Research"):
        if not query:
            st.error("Please provide a research query.")
        else:
            with st.status("🛠️ AI Agents Coordinating...", expanded=True) as status:
                st.write("📡 Ingesting papers from arXiv...")
                papers = fetch_papers(query=query, max_results=num_papers)
                
                st.write(f"🧩 Processing and Chunking...")
                for paper in papers:
                    chunks = chunk_text(paper["summary"], chunk_size=c_size)
                    for chunk in chunks:
                        vector = embed_text(chunk)
                        add_embedding(vector, {"title": paper["title"], "chunk": chunk})

                st.write("🧠 Retrieving Semantic Context...")
                query_vector = embed_text(query)
                results = search_embedding(query_vector, k=top_k)
                
                status.update(label="Analysis Complete", state="complete")

            col1, col2 = st.columns([1, 1])

            with col1:
                st.subheader("📍 Knowledge Retrieval")
                for r in results:
                    with st.expander(f"📄 {r['title'][:60]}..."):
                        st.write(r['chunk'])

            with col2:
                st.subheader("📝 AI Synthetic Report")
                with st.spinner("Generating summary..."):
                    report = summarize_chunks(results)
                    
                    if not report:
                        st.error("Summarization failed.")
                    else:
                        st.markdown(f'<div class="report-box">{report}</div>', unsafe_allow_html=True)
                        st.code(report, language=None) # Clickable copy-box
    st.markdown('</div>', unsafe_allow_html=True)
