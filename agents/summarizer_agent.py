# agents/summarizer_agent.py

from transformers import pipeline

# Load summarization model
summarizer = pipeline(
    "summarization",
    model="facebook/bart-large-cnn"
)

def summarize_chunks(chunks):
    """
    Summarize retrieved text chunks.
    """
    combined_text = " ".join([c["chunk"] for c in chunks])

    # limit input size
    combined_text = combined_text[:2000]

    summary = summarizer(
        combined_text,
        max_length=200,
        min_length=80,
        do_sample=False
    )

    return summary[0]["summary_text"]
