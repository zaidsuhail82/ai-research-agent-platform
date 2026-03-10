import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
from data_pipeline.paper_ingestion import fetch_papers
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks

# -------------------------
# 1. PAGE CONFIGURATION
# -------------------------
st.set_page_config(
    page_title="Zaid AI | Research Platform",
    page_icon="media/logo.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -------------------------
# 2. CUSTOM CSS
# -------------------------
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    .report-box { 
        padding: 20px; 
        border-radius: 12px; 
        background-color: #ffffff; 
        border-left: 6px solid #00bcd4;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        white-space: pre-wrap;      
        word-wrap: break-word;     
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 1.05rem;
        line-height: 1.6;
        color: #1e1e1e;
        min-height: 50px; 
        max-height: 600px;
        overflow-y: auto;          
    }

    .citation-card {
        padding: 15px;
        background-color: #e0f7fa;
        border-radius: 8px;
        border: 1px solid #00bcd4;
        margin-bottom: 10px;
    }

    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #00bcd4; 
        color: white;
        font-weight: bold;
        border: none;
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

# -------------------------
# 4. SIDEBAR
# -------------------------
with st.sidebar:
    logo_path = "media/logo.png"
    if os.path.exists(logo_path):
        st.image(logo_path, width=200)
    else:
        st.title("Synthetic Loop AI")
    
    st.info("""
**Architect:** M. Zaid Suhail  
*Applied AI & Electrical Engineer*

**Status:** 🟢 Operational  
**Core:** RAG + BART-Large
""")
    
    st.divider()
    st.header("⚙️ Parameters")
    num_papers = st.slider("Papers to Ingest", 1, 10, 5)
    c_size = st.select_slider("Chunk Granularity", options=[300, 500, 800, 1200], value=500)
    top_k = st.number_input("Retrieval Top-K", value=5)

# -------------------------
# 5. MAIN INTERFACE
# -------------------------
# 4. MAIN INTERFACE
st.title("🔬 Autonomous AI Research Agent")

# Enhanced Branding for your name
st.markdown("""
    <div style="margin-top: -15px; margin-bottom: 20px;">
        <span style="color: #6c757d; font-size: 1.1rem; opacity: 0.8;">
            A Persistent Learning Loop for Scientific Discovery | 
        </span>
        <span style="color: #00bcd4; font-size: 1.25rem; font-weight: 800; letter-spacing: 0.5px;">
            Engineered by M. Zaid Suhail
        </span>
    </div>
    """, unsafe_allow_html=True)

# --- CITATION GENERATOR SECTION ---
with st.expander("🔖 Citation Generator (arXiv)", expanded=False):
    cite_url = st.text_input("Paste arXiv Paper URL for Citation")
    if cite_url:
        meta = get_arxiv_metadata(cite_url)
        if meta:
            ieee = f"{meta['authors']}, \"{meta['title']},\" arXiv preprint, {meta['year']}."
            harvard = f"{meta['authors']} ({meta['year']}) '{meta['title']}', arXiv preprint."
            
            st.markdown(f"**IEEE:**")
            st.code(ieee, language=None)
            st.markdown(f"**Harvard:**")
            st.code(harvard, language=None)
        else:
            st.error("Invalid arXiv URL or metadata not found.")

st.divider()

# --- RESEARCH SECTION ---
query = st.text_input("Enter Research Topic", placeholder="e.g., Neural Ordinary Differential Equations")

if st.button("🚀 Execute Autonomous Research"):
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

