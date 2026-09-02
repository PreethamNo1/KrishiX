"""LangGraph orchestration for the agricultural question-answering agents.

Flow
----
1. ``researcher``  - studies the raw question, normalizes it, and produces a
   clear research brief containing the canonical question, sub-focus areas,
   and any region/context hints.
2. ``web_agent``   - browses the live web (DuckDuckGo) for relevant, current
   information on the question.
3. ``lit_agent``   - gathers information from free literature / general
   knowledge sources (no external network) for the question.
4. ``synthesizer`` - merges the outputs of both research agents into a single,
   coherent, farmer-friendly paragraph.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, TypedDict

from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langgraph.graph import StateGraph, END

from app.agents.utils import get_agent_llm, get_web_search_tool
from app.config import settings

logger = logging.getLogger("krishix.agents.qa")


class QnAState(TypedDict, total=False):
    question: str
    brief: str
    web_findings: str
    literature_findings: str
    answer: str


# --- Prompts ---------------------------------------------------------------

RESEARCH_BRIEF_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are the research planner for an agricultural question-answering "
                "system. Study the incoming farmer question carefully. Produce a clear "
                "research brief that another agent can use to search and gather "
                "information.\n\n"
                "Output the brief as PLAIN TEXT containing:\n"
                "- The canonical question rewritten clearly.\n"
                "- 2-4 specific sub-topics / keywords to search for.\n"
                "- Any context hints (region, crop, season, language).\n"
                "Keep it under 200 words. Do not include markdown headings."
            ),
        ),
        ("human", "Question: {question}"),
    ]
)

WEB_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a web research agent. Using the search tool, retrieve current, "
                "reliable information relevant to the research brief. Prioritize "
                "authoritative agricultural sources. Synthesize your findings into a "
                "concise bullet summary with key facts, figures, and source hints. "
                "Note explicitly if the web search returns nothing reliable."
            ),
        ),
        ("human", "Research brief:\n{brief}"),
    ]
)

LITERATURE_AGENT_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a domain-knowledge literature agent. Using your own agricultural "
                "knowledge and well-established free/public-domain knowledge (FAO, "
                "agricultural extension bulletins, ICAR notes, seed catalogs, agronomy "
                "textbooks), answer the research brief. Do NOT invent fabricated "
                "statistics; only give information you are reasonably confident about. "
                "Provide a concise bullet summary."
            ),
        ),
        ("human", "Research brief:\n{brief}"),
    ]
)

SYNTHESIZER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            (
                "You are a synthesis agent. Merge the two research summaries below into "
                "ONE single, coherent, farmer-friendly paragraph (no bullets, no "
                "headings). The answer should be clear, practical, authoritative, and "
                "in simple language suitable for a rural farmer. Where the two sources "
                "conflict, prefer the more conservative/reliable claim and keep the "
                "answer concise (under ~150 words)."
            ),
        ),
        (
            "human",
            (
                "Question: {question}\n\n"
                "WEB findings:\n{web_findings}\n\n"
                "LITERATURE findings:\n{literature_findings}\n\n"
                "Write the single synthesized paragraph now."
            ),
        ),
    ]
)


# --- Node implementations --------------------------------------------------

def researcher_node(state: QnAState) -> Dict[str, Any]:
    """Study the question and produce a research brief."""
    llm = get_agent_llm(temperature=0.2)
    chain = RESEARCH_BRIEF_PROMPT | llm | StrOutputParser()
    brief = chain.invoke({"question": state["question"]})
    return {"brief": brief}


def web_agent_node(state: QnAState) -> Dict[str, Any]:
    """Browse the web for relevant, current information."""
    llm = get_agent_llm(temperature=0.2).bind_tools([get_web_search_tool()])
    chain = WEB_AGENT_PROMPT | llm | StrOutputParser()
    findings = chain.invoke({"brief": state["brief"]})
    return {"web_findings": findings}


def literature_agent_node(state: QnAState) -> Dict[str, Any]:
    """Gather information from free literature / general knowledge."""
    llm = get_agent_llm(temperature=0.2)
    chain = LITERATURE_AGENT_PROMPT | llm | StrOutputParser()
    findings = chain.invoke({"brief": state["brief"]})
    return {"literature_findings": findings}


def synthesizer_node(state: QnAState) -> Dict[str, Any]:
    """Merge both research outputs into a single paragraph."""
    llm = get_agent_llm(temperature=0.3)
    chain = SYNTHESIZER_PROMPT | llm | StrOutputParser()
    answer = chain.invoke(
        {
            "question": state["question"],
            "web_findings": state.get("web_findings", ""),
            "literature_findings": state.get("literature_findings", ""),
        }
    )
    return {"answer": answer}


# --- Graph construction ----------------------------------------------------

def build_qa_graph():
    """Build and return the question-answering LangGraph."""
    graph = StateGraph(QnAState)

    graph.add_node("researcher", researcher_node)
    graph.add_node("web_agent", web_agent_node)
    graph.add_node("literature_agent", literature_agent_node)
    graph.add_node("synthesizer", synthesizer_node)

    graph.set_entry_point("researcher")
    graph.add_edge("researcher", "web_agent")
    graph.add_edge("researcher", "literature_agent")
    graph.add_edge("web_agent", "synthesizer")
    graph.add_edge("literature_agent", "synthesizer")
    graph.add_edge("synthesizer", END)

    return graph.compile()


# Cached compiled workflow
_qa_app = None


def get_qa_app():
    """Return the compiled Q&A workflow (cached after first call)."""
    global _qa_app
    if _qa_app is None:
        _qa_app = build_qa_graph()
    return _qa_app


def answer_agricultural_question(question: str) -> str:
    """Run the full Q&A orchestration and return the synthesized answer."""
    app = get_qa_app()
    result = app.invoke({"question": question})
    return result.get("answer", "").strip()
