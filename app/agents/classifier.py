"""Intent classifier for incoming farmer voice transcriptions.

Decides whether an incoming message is a *sell offer* (route to the
buyer-matching pipeline) or an *agricultural question* (route to the
Q&A agent orchestration).
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, Literal

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.agents.utils import get_agent_llm

logger = logging.getLogger("krishix.agents.classifier")

IntentType = Literal["offer", "question", "unknown"]


CLASSIFIER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are an agricultural intent classifier for KrishiX, a voice-first "
                "marketplace for farmers. You receive the English transcription of a "
                "farmer's voice message and must classify its intent.\n\n"
                "Classify the message into exactly one of the following intents:\n"
                "- 'offer': the farmer wants to SELL produce (mentions a crop, quantity, "
                "or location to sell).\n"
                "- 'question': the farmer is ASKING for agricultural information, advice, "
                "or guidance (e.g. pest control, sowing time, weather, market price, "
                "fertilizer, seeds, disease).\n"
                "- 'unknown': it is neither clearly an offer nor a question.\n\n"
                "Respond with ONLY a valid JSON object and strictly the keys "
                "__intent, __confidence, __reason__. __intent must be one of "
                "'offer', 'question' or 'unknown'. "
                "__confidence is a float between 0 and 1. "
                "__reason is a short one-sentence justification.\n"
                "Do not include any other text, markdown, or code fences."
            ),
        ),
        ("human", "{message}"),
    ]
)


def classify_intent(message: str) -> Dict[str, Any]:
    """Classify an incoming message into an intent node.

    Returns a dict with keys ``__intent``, ``__confidence`` and ``__reason``.
    Falls back to ``unknown`` on any error.
    """
    if not message or not message.strip():
        return {
            "__intent": "unknown",
            "__confidence": 0.0,
            "__reason": "Empty message.",
        }

    try:
        llm = get_agent_llm(temperature=0.0)
        chain = CLASSIFIER_PROMPT | llm | StrOutputParser()
        raw = chain.invoke({"message": message.strip()})
        data = json.loads(raw)
        intent = data.get("__intent", "unknown")
        if intent not in {"offer", "question", "unknown"}:
            intent = "unknown"
        return {
            "__intent": intent,
            "__confidence": float(data.get("__confidence", 0.0)),
            "__reason": str(data.get("__reason", "")),
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("Intent classification failed: %s", e)
        return {
            "__intent": "unknown",
            "__confidence": 0.0,
            "__reason": f"Classification error: {e}",
        }
