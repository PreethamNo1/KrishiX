"""Shared utilities for the agent orchestration package."""
from __future__ import annotations

import logging
from functools import lru_cache

from langchain_openai import ChatOpenAI
from langchain_community.tools import DuckDuckGoSearchRun

from app.config import settings

logger = logging.getLogger("krishix.agents")


def get_agent_llm(temperature: float = 0.3) -> ChatOpenAI:
    """Build a ChatOpenAI instance pointed at OpenRouter's API.

    OpenRouter exposes an OpenAI-compatible interface, so ChatOpenAI is
    used with the OpenRouter base URL and model id.
    """
    if not settings.OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY is not configured in .env"
        )
    return ChatOpenAI(
        model=settings.OR_AGENT_MODEL,
        temperature=temperature,
        base_url="https://openrouter.ai/api/v1",
        api_key=settings.OPENROUTER_API_KEY,
        default_headers={
            "HTTP-Referer": "https://krishix.local",
            "X-Title": "KrishiX Agri Q&A",
        },
    )


@lru_cache(maxsize=1)
def get_web_search_tool() -> DuckDuckGoSearchRun:
    """Return a cached DuckDuckGo web-search tool (no API key required)."""
    return DuckDuckGoSearchRun(
        backend="text",
    )


def require_agent_config() -> None:
    """Raise if the agent orchestration cannot be configured."""
    get_agent_llm()
