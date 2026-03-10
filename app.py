import streamlit as st
import os
from data_pipeline.paper_ingestion import fetch_papers
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks

# 1. PAGE CONFIGURATION
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
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        height: 3.5em; 
        background-color: #00bcd4; 
        color: white;
        font-weight: bold;
        border: none;
    }
    .report-box { 
        padding: 25px; 
        border-radius: 12px; 
        background-color: white; 
        border-left: 6px solid #00bcd4;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
        font-family: 'Segoe UI', sans-serif;
        line-height: 1.6;
    }
    .error-box {
        padding: 15px;
        background-color: #ffeeee;
        border-left: 5px solid #ff4b4b;
        color: #990000;
        border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR (Branding & Parameters)
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

# 4. MAIN INTERFACE
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
            for paper in papers:
                chunks = chunk_text(paper["summary"], chunk_size=c_size)
                for chunk in chunks:
                    vector = embed_text(chunk)
                    add_embedding(vector, {"title": paper["title"], "chunk": chunk})

            st.write("🧠 Retrieving Semantic Context...")
            query_vector = embed_text(query)
            results = search_embedding(query_vector, k=top_k)
            
            status.update(label="Analysis Complete", state="complete")

        # 5. RESULT DISPLAY
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
                
                # Check if report is an error or actual text
                if "Error" in report or "supported" in report:
                    st.markdown(f'<div class="error-box">{report}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="report-box">{report}</div>', unsafe_allow_html=True)
                    st.download_button("📥 Download Report", data=report, file_name="Research_Report.txt")
