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
            return result[0].get("summary_text", "") if isinstance(result, list) else ""
        return None
    except Exception:
        return None

def summarize_chunks(results):
    """
    Standard RAG summary for the Autonomous Agent.
    """
    context = " ".join([r['chunk'] for r in results])
    payload = {
        "inputs": context[:3000],
        "parameters": {"max_length": 250, "min_length": 80, "do_sample": False}
    }
    return query_hf_router(payload) or "Summarization failed."

def generate_lit_review(content, style="IEEE", word_count=100):
    """
    ENGINEERED SYNTHESIS:
    Calculates dynamic token limits based on your word count selection
    to ensure the AI doesn't just stick to 40-50 words.
    """
    if not content:
        return "No content provided."

    # Senior Level Logic: Map word count to token constraints
    # BART tokens are roughly 1.3x word count.
    limits = {
        30:  {"min": 25,  "max": 45},
        50:  {"min": 45,  "max": 75},
        80:  {"min": 70,  "max": 110},
        100: {"min": 90,  "max": 140},
        150: {"min": 140, "max": 200},
        200: {"min": 190, "max": 270},
        250: {"min": 240, "max": 350}
    }
    
    # Fallback to 100 if something goes wrong
    param = limits.get(int(word_count), limits[100])

    # Guiding the model based on style
    prompt = f"Write a formal {style} style academic literature review: {content}"

    payload = {
        "inputs": prompt[:3000],
        "parameters": {
            "max_length": param["max"],
            "min_length": param["min"],
            "do_sample": False,
            "repetition_penalty": 1.2 # Prevents the AI from repeating itself in longer reviews
        }
    }

    result = query_hf_router(payload)
    return result or "Literature review generation failed."
