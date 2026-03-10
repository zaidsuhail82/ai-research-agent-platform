# agents/summarizer_agent.py
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
import torch

# Model name
MODEL_NAME = "facebook/bart-large-cnn"

# Load model & tokenizer locally
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, local_files_only=True)
model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME, local_files_only=True)

# Use GPU if available, otherwise CPU
device = 0 if torch.cuda.is_available() else -1

# Create summarization pipeline
summarizer = pipeline(
    task="summarization",
    model=model,
    tokenizer=tokenizer,
    device=device
)

def summarize_chunks(chunks):
    """
    Summarize a list of text chunks using local BART model.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine all chunks into one string
    text = " ".join([c["chunk"] for c in chunks])

    # Truncate very long text
    text = text[:3000]

    # Generate summary
    summary = summarizer(
        text,
        max_length=200,
        min_length=50,
        do_sample=False
    )

    return summary[0]["summary_text"]
