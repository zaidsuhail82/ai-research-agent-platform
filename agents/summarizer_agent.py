# agents/summarizer_agent.py
import requests
import streamlit as st

# Hugging Face Inference API (no local model needed)
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {st.secrets['HUGGINGFACE_TOKEN']}"}

def summarize_chunks(chunks):
    """
    Summarize a list of text chunks using Hugging Face API.
    Returns a clean logical summary.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine chunks
    text_to_summarize = " ".join([c["chunk"] for c in chunks])
    text_to_summarize = text_to_summarize[:3000]  # truncate for API limits

    payload = {
        "inputs": text_to_summarize,
        "parameters": {"max_length": 200, "min_length": 50, "do_sample": False}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()

        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return f"Error generating summary: {result}"

    except Exception as e:
        return f"Summarization failed: {str(e)}"
