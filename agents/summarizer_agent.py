import requests
import streamlit as st

# 2026 Router Endpoint
API_URL = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"
headers = {"Authorization": f"Bearer {st.secrets['HUGGINGFACE_TOKEN']}"}

def query_hf_router(payload):
    """Internal helper to communicate with the Hugging Face Router."""
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get("summary_text", "")
            return "Unexpected JSON format from API."
        return f"API Error: {response.status_code}"
    except Exception as e:
        return f"Connection failed: {str(e)}"

def summarize_chunks(results):
    """
    Standard RAG summary for the Global Research Tool.
    """
    context = " ".join([r['chunk'] for r in results])
    payload = {
        "inputs": context[:3000],
        "parameters": {"max_length": 250, "min_length": 80, "do_sample": False}
    }
    return query_hf_router(payload) or "Summarization failed."

def generate_lit_review(content, style="IEEE", word_count=100):
    """
    Professional Synthesis Agent for Literature Reviews.
    Note: The 'Last Name, F.' part is prepended in app.py.
    """
    if not content:
        return "No content provided."

    # Dynamic BART constraints (Approx 1.3 tokens per word)
    limits = {
        30:  {"min": 25,  "max": 45},
        50:  {"min": 45,  "max": 75},
        80:  {"min": 70,  "max": 110},
        100: {"min": 90,  "max": 140},
        150: {"min": 140, "max": 200},
        200: {"min": 190, "max": 270},
        250: {"min": 240, "max": 350}
    }
    
    param = limits.get(int(word_count), limits[100])

    # Senior-Level Engineering Prompt
    prompt = f"Critically summarize the key findings, methodology, and scientific contribution of this text in a formal {style} academic tone: {content}"

    payload = {
        "inputs": prompt[:3000],
        "parameters": {
            "max_length": param["max"],
            "min_length": param["min"],
            "do_sample": False,
            "repetition_penalty": 1.2 
        }
    }

    result = query_hf_router(payload)
    return result or "Literature review generation failed."
