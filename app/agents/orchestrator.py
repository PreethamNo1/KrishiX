"""High-level agent orchestration entry points.

Exposes a single ``route_message`` helper that the FastAPI pipeline can call
to classify an incoming farmer message and, when it is a question, run the
Q&A agent workflow.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from app.agents.classifier import classify_intent
from app.agents.qa import answer_agricultural_question

logger = logging.getLogger("krishix.agents.orchestrator")


def route_message(message: str) -> Dict[str, Any]:
    """Classify a message and, if it is a question, produce an answer.

    Returns a dict describing the routing decision and, for questions, the
    synthesized answer:

    .. code-block:: python
        {
            "intent": "question",
            "confidence": 0.97,
            "reason": "...",
            "classification": {...},
            "answer": "<synthesized paragraph>"   # only for questions
        }

    For non-question intents, ``answer`` is omitted and the caller should
    proceed with the normal buyer-matching (offer) pipeline.
    """
    classification = classify_intent(message)
    intent = classification.get("__intent", "unknown")

    result: Dict[str, Any] = {
        "intent": intent,
        "confidence": classification.get("__confidence", 0.0),
        "reason": classification.get("__reason", ""),
        "classification": classification,
    }

    if intent == "question":
        try:
            result["answer"] = answer_agricultural_question(message)
        except Exception as e:  # noqa: BLE001
            logger.error("Q&A orchestration failed: %s", e)
            result["answer_error"] = str(e)

    return result
