# agents/summarizer_agent.py
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline

# Load the model and tokenizer explicitly
model_name = "facebook/bart-large-cnn"
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# Create the pipeline by passing the model and tokenizer directly
summarizer = pipeline(
    "summarization", 
    model=model, 
    tokenizer=tokenizer
)

def summarize_chunks(chunks):
    """
    Summarize retrieved text chunks using BART.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine text from chunks (using the structure from your test_pipeline)
    combined_text = " ".join([c["chunk"] for c in chunks])

    # BART has a max input of 1024 tokens (~3000-4000 characters)
    combined_text = combined_text[:3000]

    print("--- Running AI Summarization (BART) ---")
    
    summary = summarizer(
        combined_text, 
        max_length=150, 
        min_length=50, 
        do_sample=False
    )

    return summary[0]["summary_text"]
