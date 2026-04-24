"""LLM configuration — centralized Gemini LLM and embeddings setup.

Provides factory functions for the Google Gemini chat model and
embedding model used across both SQL and RAG modes.
"""

import os
import time
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

# Load .env from project root (one level up from utils/)
load_dotenv(Path(__file__).parent.parent / ".env")

# Models to try in order — falls back if one is overloaded
_LLM_MODELS = ["gemini-3.1-flash-lite-preview", "gemini-2.5-flash-lite", "gemini-2.5-flash"]


def _resolve_api_key(api_key: str | None) -> str:
    """Return an explicit key or fall back to the environment variable.

    Args:
        api_key: An explicit API key, or None to read from env.

    Returns:
        The resolved API key string.

    Raises:
        ValueError: If no key is found in either the argument or env.
    """
    key = api_key or os.environ.get("GOOGLE_API_KEY")
    if not key:
        raise ValueError(
            "Google API key not found. Either pass api_key= or set "
            "GOOGLE_API_KEY in your .env file. "
            "Get a key at https://aistudio.google.com/apikey"
        )
    return key


def get_llm(api_key: str | None = None) -> ChatGoogleGenerativeAI:
    """Create a ChatGoogleGenerativeAI instance with automatic model fallback.

    Tries models in order: gemini-2.0-flash → gemini-2.0-flash-lite →
    gemini-2.5-flash. If one is overloaded (503), it falls back to the next.

    Args:
        api_key: Optional explicit API key. Falls back to GOOGLE_API_KEY env var.

    Returns:
        A configured ChatGoogleGenerativeAI ready for invocation.

    Raises:
        ValueError: If no API key is available.
    """
    key = _resolve_api_key(api_key)
    return ChatGoogleGenerativeAI(
        model=_LLM_MODELS[0],
        temperature=0,
        google_api_key=key,
        max_retries=3,
    )


def get_embeddings(api_key: str | None = None) -> GoogleGenerativeAIEmbeddings:
    """Create a GoogleGenerativeAIEmbeddings instance.

    Args:
        api_key: Optional explicit API key. Falls back to GOOGLE_API_KEY env var.

    Returns:
        A configured GoogleGenerativeAIEmbeddings for vector operations.

    Raises:
        ValueError: If no API key is available.
    """
    key = _resolve_api_key(api_key)
    return GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=key,
    )
