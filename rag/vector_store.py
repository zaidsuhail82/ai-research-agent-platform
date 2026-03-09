# vector_store.py

import faiss
import numpy as np

dimension = 384  # same as all-MiniLM-L6-v2
index = faiss.IndexFlatL2(dimension)  # L2 similarity

# To store metadata for each vector
metadata_store = []

def add_embedding(embedding, metadata=None):
    index.add(np.array([embedding]))
    metadata_store.append(metadata)

def search_embedding(query_embedding, k=5):
    D, I = index.search(np.array([query_embedding]), k)
    results = []
    for idx in I[0]:
        if idx < len(metadata_store):
            results.append(metadata_store[idx])
    return results
