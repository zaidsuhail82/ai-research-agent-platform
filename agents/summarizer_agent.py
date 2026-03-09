# agents/summarizer_agent.py
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch

# Load the model and tokenizer explicitly
model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

# Move to GPU if available
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

def summarize_chunks(chunks):
    """
    Summarize retrieved text chunks using BART's native generation method.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine text from chunks
    text_to_summarize = " ".join([c["chunk"] for c in chunks])
    
    # BART limit check (approx 1024 tokens)
    inputs = tokenizer(text_to_summarize, max_length=1024, truncation=True, return_tensors="pt").to(device)

    print(f"--- Running AI Summarization (BART) on {device.upper()} ---")

    # Generate Summary IDs
    summary_ids = model.generate(
        inputs["input_ids"], 
        num_beams=4, 
        min_length=50, 
        max_length=200, 
        early_stopping=True
    )

    # Decode back to readable text
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary
