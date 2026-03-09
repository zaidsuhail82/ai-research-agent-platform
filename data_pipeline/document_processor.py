# document_processor.py

def chunk_text(text, chunk_size=500, overlap=50):
    """
    Split text into chunks with overlap for better context in embeddings.
    :param text: str, full text
    :param chunk_size: int, number of characters per chunk
    :param overlap: int, number of overlapping characters between chunks
    :return: list of chunks
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap  # move start, keep overlap

    return chunks


if __name__ == "__main__":
    sample_text = "Machine learning is transforming autonomous vehicles. Reinforcement learning and deep learning techniques are applied in self-driving car control systems."
    chunks = chunk_text(sample_text, chunk_size=50, overlap=10)
    for i, c in enumerate(chunks):
        print(f"Chunk {i+1}: {c}\n")
