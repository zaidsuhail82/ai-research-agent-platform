import requests
import streamlit as st

# UPDATED: Using the 2026 Router Endpoint
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"

# Accessing the token from Streamlit Secrets
headers = {"Authorization": f"Bearer {st.secrets['HUGGINGFACE_TOKEN']}"}

def summarize_chunks(chunks):
    """
    Summarize a list of text chunks using Hugging Face Router API.
    Returns a clean logical summary string.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine chunks into a single context string
    text_to_summarize = " ".join([c["chunk"] for c in chunks])
    text_to_summarize = text_to_summarize[:3000]  # Respecting context window limits

    payload = {
        "inputs": text_to_summarize,
        "parameters": {
            "max_length": 250, 
            "min_length": 80, 
            "do_sample": False
        }
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            result = response.json()
            # Extract only the summary text string
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("summary_text", "No summary text returned.")
            return "Unexpected JSON format from API."
        
        # Specific handling for the 410 Gone / Migration error
        elif response.status_code == 410 or "supported" in response.text:
            return "⚠️ API Migration Error: The Hugging Face endpoint has moved. Ensure you are using the 'router.huggingface.co' URL."
        
        else:
            return f"Agent Error ({response.status_code}): {response.text}"

    except Exception as e:
        return f"Summarization failed: {str(e)}"
