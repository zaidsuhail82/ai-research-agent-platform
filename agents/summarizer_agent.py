import requests
import streamlit as st

# We use the Hugging Face Inference API to avoid memory crashes
API_URL = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"
# Access your token from Streamlit Secrets
headers = {"Authorization": f"Bearer {st.secrets['HUGGINGFACE_TOKEN']}"}

def summarize_chunks(chunks):
    """
    Summarize retrieved text chunks using Hugging Face Inference API.
    """
    if not chunks:
        return "No text provided for summarization."

    # Combine text from chunks
    text_to_summarize = " ".join([c["chunk"] for c in chunks])
    
    # Prepare the payload for the API
    payload = {
        "inputs": text_to_summarize,
        "parameters": {"max_length": 200, "min_length": 50, "do_sample": False}
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        result = response.json()
        
        # The API returns a list with a dictionary
        if isinstance(result, list) and "summary_text" in result[0]:
            return result[0]["summary_text"]
        else:
            return f"Error: {result}"
            
    except Exception as e:
        return f"Summarization failed: {str(e)}"
