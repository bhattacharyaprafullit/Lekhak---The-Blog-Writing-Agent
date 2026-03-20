"""
nodes/research.py
-----------------
The Research node runs Tavily searches and deduplicates the raw results
into a clean list of EvidenceItem objects that subsequent nodes can cite.

It only runs when the Router marks needs_research=True.
The LLM acts as a synthesiser here — it receives raw search results and
returns a deduplicated, clean EvidencePack.
"""

from typing import List

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import llm
from app.models.schemas import EvidencePack, EvidenceItem, State

RESEARCH_SYSTEM = """You are a research synthesizer for technical writing.

Given raw web search results, produce a deduplicated list of EvidenceItem objects.
Respond in JSON format.

Rules:
- Only include items with a non-empty url.
- Prefer relevant + authoritative sources.
- If published date is present, keep as YYYY-MM-DD. If missing, set null.
- Keep snippets short.
- Deduplicate by URL.
- Return MAX 6 evidence items.
"""


def _tavily_search(query: str, max_results: int = 2) -> List[dict]:
    """Run a single Tavily query and normalise the result shape."""
    tool = TavilySearchResults(max_results=max_results)
    results = tool.invoke({"query": query})

    normalized: List[dict] = []
    for r in results or []:
        normalized.append(
            {
                "title": r.get("title") or "",
                "url": r.get("url") or "",
                # Truncate snippet to keep LLM context lean
                "snippet": (r.get("content") or r.get("snippet") or "")[:200],
                "published_at": r.get("published_date") or r.get("published_at"),
                "source": r.get("source"),
            }
        )
    return normalized


def research_node(state: State) -> dict:
    # Only use first 3 queries to control token spend
    queries = (state.get("queries", []) or [])[:3]
    max_results = 2

    raw_results: List[dict] = []
    for q in queries:
        raw_results.extend(_tavily_search(q, max_results=max_results))

    if not raw_results:
        return {"evidence": []}

    extractor = llm.with_structured_output(EvidencePack, method="json_mode")
    pack = extractor.invoke(
        [
            SystemMessage(content=RESEARCH_SYSTEM),
            # Send only first 4 results to keep prompt size manageable
            HumanMessage(content=f"Raw results:\n{raw_results[:4]}"),
        ]
    )

    # Final dedup by URL (LLM might still return duplicates)
    dedup = {}
    for e in pack.evidence:
        if e.url:
            dedup[e.url] = e

    return {"evidence": list(dedup.values())}
