from __future__ import annotations

import requests


def ask_local_ollama(prompt: str, model: str = "llama3.1") -> str:
    """Attempt a local Ollama chat call and return a safe fallback on failure."""
    url = "http://localhost:11434/api/generate"
    payload = {"model": model, "prompt": prompt, "stream": False}
    try:
        response = requests.post(url, json=payload, timeout=8)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "No response from local assistant.")
    except Exception:
        return (
            "Local AI assistant is currently offline. Start Ollama locally and pull a model "
            "(example: `ollama pull llama3.1`) for private, on-device help."
        )
