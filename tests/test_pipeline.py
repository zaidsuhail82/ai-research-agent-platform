# tests\test_pipeline.py

import sys
import os

# Add project root to Python path (Windows-friendly)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Now imports will work
from data_pipeline.paper_ingestion import fetch_papers
from data_pipeline.document_processor import chunk_text
from rag.embeddings import embed_text
from rag.vector_store import add_embedding, search_embedding
from agents.summarizer_agent import summarize_chunks

def main():
    print("Fetching sample papers from arXiv...")
    papers = fetch_papers(query="reinforcement learning autonomous vehicles", max_results=3)

    print(f"Fetched {len(papers)} papers.\n")

    # Process each paper
    for paper in papers:
        print(f"Processing paper: {paper['title']}")
        chunks = chunk_text(paper["summary"], chunk_size=200, overlap=50)
        for chunk in chunks:
            vector = embed_text(chunk)
            add_embedding(vector, metadata={"title": paper["title"], "chunk": chunk})

    print("\nTest semantic search:")
    query = "self-driving car safety"
    query_vector = embed_text(query)
    results = search_embedding(query_vector, k=3)

    print("\nTop 3 relevant chunks:")
    for r in results:
        print(f"- {r['title']}: {r['chunk'][:150]}...\n")

print("\nGenerating research summary...\n")

summary = summarize_chunks(results)

print("Research Summary:\n")
print(summary)

if __name__ == "__main__":
    main()


