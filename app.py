# app.py
import streamlit as st
import os
from data_pipeline.paper_ingestion import fetch_papers
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks

st.set_page_config(
    page_title="Zaid AI | Research Platform",
    page_icon="logo.png", # This puts your logo in the browser tab!
    layout="wide"
)


# 1. PAGE CONFIGURATION (Modern Look)
st.set_page_config(
    page_title="Zaid | AI Research Platform",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. CUSTOM CSS (For that "High-End" feel)
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .report-box { padding: 20px; border-radius: 10px; background-color: white; border-left: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# 3. SIDEBAR (Personal Branding & Logo)
with st.sidebar:
    if os.path.exists("logo.png"):
        st.image("logo.png", width=200)
    
    st.title("Project Credits")
    st.markdown("""
    **Architect:** M. Zaid Suhail  
    *MSc Applied Artificial Intelligence* *MSc Electrical Engineering*
    
    ---
    **System Status:** 🟢 Operational  
    **Model:** BART-Large-CNN  
    **Database:** In-Memory Vector Index
    """)
    
    st.divider()
    st.header("⚙️ Research Parameters")
    # Using Session State to ensure these values are locked in during the run
    num_papers = st.slider("Papers to Ingest", 1, 10, 5)
    c_size = st.select_slider("Chunk Granularity", options=[300, 500, 800, 1200], value=500)
    top_k = st.number_input("Retrieval Top-K", value=5)

# 4. MAIN INTERFACE
st.title("🔬 Autonomous AI Research Agent")
st.caption("Engineered by M. Zaid Suhail | London South Bank University")

query = st.text_input("Enter Research Topic", placeholder="e.g., Neural Ordinary Differential Equations in Robotics")

if st.button("🚀 Execute Autonomous Research"):
    if not query:
        st.error("Please provide a research query.")
    else:
        # FIX: CLEAR PREVIOUS DATA
        # To make results dynamic, we simulate a fresh environment per run
        with st.status("🛠️ AI Agents Coordinating...", expanded=True) as status:
            
            st.write("📡 Ingesting papers from arXiv...")
            papers = fetch_papers(query=query, max_results=num_papers)
            
            st.write(f"🧩 Processing and Chunking at {c_size} tokens...")
            for paper in papers:
                # We pass the slider value here to make it dynamic!
                chunks = chunk_text(paper["summary"], chunk_size=c_size)
                for chunk in chunks:
                    vector = embed_text(chunk)
                    add_embedding(vector, {"title": paper["title"], "chunk": chunk})

            st.write("🧠 Retrieving Semantic Context...")
            query_vector = embed_text(query)
            # Use the 'top_k' from user input
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
            with st.spinner("BART Agent generating abstractive summary..."):
                # We pass the results to the agent
                report = summarize_chunks(results)
                st.markdown(f'<div class="report-box">{report}</div>', unsafe_allow_html=True)
                
                # Professional Feature: Download Button
                st.download_button(
                    label="📥 Download Research Report",
                    data=report,
                    file_name=f"Research_Report_{query.replace(' ', '_')}.txt",
                    mime="text/plain"
                )

