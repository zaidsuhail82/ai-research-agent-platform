import streamlit as st
import os
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

# 2. CUSTOM CSS (Engineering Aesthetic)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    
    /* The Report Container */
    .report-box { 
        padding: 20px; 
        border-radius: 12px; 
        background-color: #ffffff; 
        border-left: 6px solid #00bcd4;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        
        /* FIX FOR SCROLLING LINE: */
        white-space: pre-wrap;      /* Forces text to wrap to the next line */
        word-wrap: break-word;     /* Breaks long words if necessary */
        
        font-family: 'Inter', 'Segoe UI', sans-serif;
        font-size: 1.05rem;
        line-height: 1.6;
        color: #1e1e1e;
        
        /* FIX FOR EMPTY BOX: */
        min-height: 50px; 
        max-height: 600px;
        overflow-y: auto;          /* Only scroll vertically if it's very long */
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
    """, unsafe_allow_html=True)# -------------------------
# 3. SIDEBAR
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
# 4. MAIN INTERFACE
# -------------------------
st.title("🔬 Autonomous AI Research Agent")
st.caption("A Persistent Learning Loop for Scientific Discovery | Engineered by M. Zaid Suhail")

query = st.text_input("Enter Research Topic", placeholder="e.g., Neural Ordinary Differential Equations")

if st.button("🚀 Execute Autonomous Research"):
    if not query:
        st.error("Please provide a research query.")
    else:
        with st.status("🛠️ AI Agents Coordinating...", expanded=True) as status:
            st.write("📡 Ingesting papers from arXiv...")
            papers = fetch_papers(query=query, max_results=num_papers)
            
            st.write(f"🧩 Processing and Chunking at {c_size} tokens...")
            all_chunks = []
            for paper in papers:
                chunks = chunk_text(paper["summary"], chunk_size=c_size)
                for chunk in chunks:
                    vector = embed_text(chunk)
                    add_embedding(vector, {"title": paper["title"], "chunk": chunk})
                    all_chunks.append({"title": paper["title"], "chunk": chunk})

            st.write("🧠 Retrieving Semantic Context...")
            query_vector = embed_text(query)
            results = search_embedding(query_vector, k=top_k)
            
            status.update(label="Analysis Complete", state="complete")

        # -------------------------
        # 5. RESULT DISPLAY
        # -------------------------
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📍 Knowledge Retrieval")
            for r in results:
                with st.expander(f"📄 {r['title'][:60]}..."):
                    st.write(r['chunk'])

        with col2:
            st.subheader("📝 AI Synthetic Report")
            with st.spinner("BART Agent generating summary..."):
                report = summarize_chunks(results)
                
                if not report:
                    st.markdown('<div class="error-box">Error generating summary.</div>', unsafe_allow_html=True)
                else:
                    # Modern live text box
                    st.markdown(f'<div class="report-box" id="report-box">{report}</div>', unsafe_allow_html=True)
                    
                    # Copy button
                    st.code(report, language=None)
                    st.markdown("""
                    <script>
                    function copyToClipboard(text) {
                        navigator.clipboard.writeText(text);
                        alert('Summary copied to clipboard!');
                    }
                    </script>
                    """, unsafe_allow_html=True)

