"""
LLM provider abstraction for document (vision/OCR) extraction.

Provides a unified interface over different multimodal LLM backends — Google
Gemini and any OpenAI-compatible endpoint (OpenAI, vLLM, Ollama, LM Studio,
Together, Groq, etc.) — so the rest of the application does not depend on a
specific vendor SDK. The concrete provider is selected at runtime from
environment variables.

Configuration:
    LLM_PROVIDER     "gemini" (default) or "openai"
    LLM_MODEL        Model name (defaults per provider if unset)

    Gemini:
        GOOGLE_API_KEY

    OpenAI-compatible:
        OPENAI_API_KEY
        OPENAI_BASE_URL  (default https://api.openai.com/v1)
"""

import os
import base64
from abc import ABC, abstractmethod

# Default model per provider, used when LLM_MODEL is not set.
DEFAULT_MODELS = {
    "gemini": "gemini-2.5-flash-lite",
    "openai": "gpt-4o-mini",
}


class VisionProvider(ABC):
    """Abstract base class for multimodal (image -> text) extraction backends."""

    @abstractmethod
    def extract(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        """
        Send an image plus a text prompt to the model and return its text reply.

        Args:
            image_bytes: Raw bytes of the image to analyze.
            mime_type: MIME type of the image (e.g. "image/jpeg").
            prompt: The instruction describing what to extract.

        Returns:
            The model's text response.
        """
        raise NotImplementedError


class GeminiVisionProvider(VisionProvider):
    """Vision extraction backed by Google Gemini (via the google-genai SDK)."""

    def __init__(self, api_key: str, model: str):
        import google.genai as genai

        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def extract(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                self._genai.types.Part.from_bytes(
                    data=image_bytes, mime_type=mime_type
                ),
                prompt,
            ],
        )
        return response.text


class OpenAIVisionProvider(VisionProvider):
    """Vision extraction for any OpenAI-compatible endpoint (via the openai SDK)."""

    def __init__(self, api_key: str, base_url: str, model: str):
        from openai import OpenAI

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model

    def extract(self, image_bytes: bytes, mime_type: str, prompt: str) -> str:
        # OpenAI-compatible vision input expects the image as a base64 data URL.
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        data_url = f"data:{mime_type};base64,{b64}"

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )
        return response.choices[0].message.content


def get_vision_provider() -> VisionProvider:
    """Build the vision provider selected by the LLM_PROVIDER env var."""
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model = os.getenv("LLM_MODEL") or DEFAULT_MODELS.get(provider)

    if provider == "gemini":
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY is required when LLM_PROVIDER=gemini"
            )
        return GeminiVisionProvider(api_key, model)

    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is required when LLM_PROVIDER=openai"
            )
        base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        return OpenAIVisionProvider(api_key, base_url, model)

    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r}")
