from __future__ import annotations

import os
from typing import Any, Optional

import requests

from backend.services.config import GEMINI_API_KEY


class GeminiService:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None) -> None:
        # Dynamically fetch from the environment to ensure we grab the fresh .env values
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
        
        # Explicitly default to the modern 2.5-flash model
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

    def ask(self, question: str, context: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        if not self.api_key:
            return {
                "answer": "Gemini API key is not configured. Set GEMINI_API_KEY in your environment to enable the developer assistant.",
                "model": self.model,
                "status": "not_configured",
            }

        prompt = self._build_prompt(question, context or {})
        
        try:
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
                params={"key": self.api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.2, "maxOutputTokens": 1024},
                },
                timeout=60,
            )
            
            # If the API rejects our request, don't crash the server! Return the error to the chat.
            if not response.ok:
                return {
                    "answer": f"Google AI API Error ({response.status_code}): {response.text}",
                    "model": self.model,
                    "status": "error"
                }
                
            payload = response.json()
            text = payload["candidates"][0]["content"]["parts"][0]["text"]
            return {"answer": text, "model": self.model, "status": "ok", "raw": payload}
            
        except requests.exceptions.RequestException as e:
            # Catch network timeouts or connection issues gracefully
            return {
                "answer": f"Failed to connect to the AI service: {str(e)}",
                "model": self.model,
                "status": "error"
            }

    def _build_prompt(self, question: str, context: dict[str, Any]) -> str:
        return (
            "You are an AI software quality assistant. Use the repository analysis, defect predictions, tests, bugs, "
            "and semantic search context to answer concisely with actionable engineering guidance.\n\n"
            f"Question:\n{question}\n\n"
            f"Context:\n{context}"
        )