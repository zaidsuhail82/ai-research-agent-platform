# agents/summarizer_agent.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

MODEL_NAME = "facebook/bart-large-cnn"

# Load model & tokenizer (allow downloading)
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)

# Use GPU if available, otherwise CPU
device = 0 if torch.cuda.is_available() else -1

# Summarization pipeline
summarizer = pipeline(
    task="summarization",
    model=model,
    tokenizer=tokenizer,
    device=device
)

def summarize_chunks(chunks):
    """
    Summarize a list of text chunks using BART.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine all chunks
    text = " ".join([c["chunk"] for c in chunks])
    text = text[:3000]  # truncate long input

    summary = summarizer(
        text,
        max_length=200,
        min_length=50,
        do_sample=False
    )

    return summary[0]["summary_text"]
