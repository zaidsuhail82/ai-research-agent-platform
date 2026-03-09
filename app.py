import streamlit as st
from data_pipeline.paper_ingestion import fetch_papers
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks

# Page Config
st.set_page_config(page_title="AI Research Agent", layout="wide")
st.title("🔬 AI Research Agent Platform")
st.markdown("Automated arXiv Ingestion, Semantic Search, and BART Summarization")

# Sidebar for Search Settings
with st.sidebar:
    st.header("Search Settings")
    max_results = st.slider("Number of papers to fetch", 1, 10, 3)
    chunk_size = st.number_input("Chunk Size", value=500)

# User Input
query = st.text_input("Enter a research topic (e.g., 'Neural ODEs' or 'Autonomous Driving'):")

if st.button("Start Research"):
    if query:
        with st.status("🔍 Working..."):
            # 1. Fetch
            st.write("Fetching papers from arXiv...")
            papers = fetch_papers(query=query, max_results=max_results)
            
            # 2. Process & Embed
            st.write(f"Processing {len(papers)} papers...")
            all_chunks = []
            for paper in papers:
                chunks = chunk_text(paper["summary"], chunk_size=chunk_size)
                for chunk in chunks:
                    vector = embed_text(chunk)
                    metadata = {"title": paper["title"], "chunk": chunk}
                    add_embedding(vector, metadata)
                    all_chunks.append(metadata)

            # 3. Semantic Search
            st.write("Performing semantic search...")
            query_vector = embed_text(query)
            results = search_embedding(query_vector, k=5)

        # UI LAYOUT: Left side for Chunks, Right side for Summary
        col1, col2 = st.columns([1, 1])

        with col1:
            st.subheader("📍 Relevant Chunks")
            for r in results:
                with st.expander(f"Source: {r['title'][:50]}..."):
                    st.write(r['chunk'])

        with col2:
            st.subheader("📝 AI Research Summary")
            with st.spinner("BART is thinking..."):
                summary = summarize_chunks(results)
                st.info(summary)
    else:
        st.warning("Please enter a query first!")
