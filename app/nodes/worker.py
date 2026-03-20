"""
nodes/worker.py
---------------
The Worker node writes ONE section of the blog post.

It is called in parallel for every Task in the Plan via LangGraph's Send API
(fan-out pattern). Each worker receives its own task payload independently,
writes the section Markdown, and returns (task_id, section_md) so the reducer
can sort them back into correct order.

The "scope guard" in the system prompt prevents the LLM from turning a
news-roundup section into a tutorial, which is a common drift issue.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import llm
from app.models.schemas import Task, Plan, EvidenceItem

WORKER_SYSTEM = """You are a senior technical writer and developer advocate.
Write ONE section of a technical blog post in Markdown.

Hard constraints:
- Follow the provided Goal and cover ALL Bullets in order.
- MAX 300 words per section. Stay within this limit strictly.
- Output ONLY the section content in Markdown (no blog title H1, no extra commentary).
- Start with a '## <Section Title>' heading.

Scope guard:
- If blog_kind == "news_roundup": do NOT turn this into a tutorial/how-to guide.
  Focus on summarizing events and implications only.

Grounding policy:
- If mode == open_book:
  - Do NOT introduce any claim unless supported by provided Evidence URLs.
  - Attach source as Markdown link: ([Source](URL)).
  - If not supported, write: "Not found in provided sources."
- If requires_citations == true:
  - Cite Evidence URLs for outside-world claims.

Code:
- If requires_code == true, include one minimal correct code snippet.

Style:
- Short paragraphs, bullets where helpful, code fences for code.
- Avoid fluff. Be precise and implementation-oriented.
"""


def worker_node(payload: dict) -> dict:
    """
    Receives a self-contained payload (not the full State) because LangGraph's
    Send API passes only what you explicitly include in the fanout function.
    """
    task = Task(**payload["task"])
    plan = Plan(**payload["plan"])
    evidence = [EvidenceItem(**e) for e in payload.get("evidence", [])]
    topic = payload["topic"]
    mode = payload.get("mode", "closed_book")

    bullets_text = "\n- " + "\n- ".join(task.bullets)

    # Build evidence block — max 5 items to keep the prompt tight
    evidence_text = ""
    if evidence:
        evidence_text = "\n".join(
            f"- {e.title} | {e.url} | {e.published_at or 'date:unknown'}".strip()
            for e in evidence[:5]
        )

    section_md = llm.invoke(
        [
            SystemMessage(content=WORKER_SYSTEM),
            HumanMessage(
                content=(
                    f"Blog title: {plan.blog_title}\n"
                    f"Audience: {plan.audience}\n"
                    f"Tone: {plan.tone}\n"
                    f"Blog kind: {plan.blog_kind}\n"
                    f"Topic: {topic}\n"
                    f"Mode: {mode}\n\n"
                    f"Section title: {task.title}\n"
                    f"Goal: {task.goal}\n"
                    f"Target words: {task.target_words}\n"
                    f"requires_code: {task.requires_code}\n"
                    f"requires_citations: {task.requires_citations}\n"
                    f"Bullets:{bullets_text}\n\n"
                    f"Evidence:\n{evidence_text}\n"
                )
            ),
        ]
    ).content.strip()

    return {"sections": [(task.id, section_md)]}
