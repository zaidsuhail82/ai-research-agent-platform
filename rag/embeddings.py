# embeddings.py

from sentence_transformers import SentenceTransformer

# Use a small but high-quality model for embeddings
model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_text(text):
    """
    Convert text into vector embeddings.
    :param text: str
    :return: numpy array
    """
    return model.encode(text)
