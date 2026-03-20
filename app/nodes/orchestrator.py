"""
nodes/orchestrator.py
---------------------
The Orchestrator node is the "senior technical writer" that produces the
full blog outline (a Plan) before any section writing begins.

It receives the topic, the routing mode, and any evidence gathered, then
returns a structured Plan containing 4-5 Task objects. Those Task objects
drive the parallel fan-out to worker nodes.

The system prompt includes STRICT field-name rules because LLMs sometimes
hallucinate alternative names ("title" instead of "blog_title", etc.) which
would break Pydantic validation.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import llm
from app.models.schemas import Plan, State

ORCH_SYSTEM = """You are a senior technical writer and developer advocate.
Your job is to produce a highly actionable outline for a technical blog post.
Respond in JSON format.

IMPORTANT: Return EXACTLY this JSON structure with these EXACT field names:
{
  "blog_title": "title here",
  "audience": "developers",
  "tone": "informative",
  "blog_kind": "explainer",
  "constraints": [],
  "tasks": [
    {
      "id": 1,
      "title": "Section Title",
      "goal": "One sentence goal.",
      "bullets": ["bullet one", "bullet two", "bullet three"],
      "target_words": 200,
      "tags": [],
      "requires_research": false,
      "requires_citations": false,
      "requires_code": false
    }
  ]
}

STRICT RULES:
- Use "blog_title" NOT "title".
- Use "tasks" NOT "sections".
- Use "target_words" NOT "target_word_count".
- Use "audience" and "tone" fields -- they are required.
- Create 4-5 tasks only.
- Each task: 3-4 bullets, target_words 150-250.
- blog_kind must be one of: explainer, tutorial, news_roundup, comparison, system_design.
- At least 1 task must have requires_code=true.
- Use plain ASCII characters only, no special dashes or Unicode.

Grounding rules:
- Mode closed_book: keep it evergreen, do not depend on evidence.
- Mode hybrid: use evidence for up-to-date examples, mark those sections requires_research=true and requires_citations=true.
- Mode open_book: set blog_kind as news_roundup, every section summarizes events and implications.
"""


def orchestrator_node(state: State) -> dict:
    planner = llm.with_structured_output(Plan, method="json_mode")

    evidence = state.get("evidence", [])
    mode = state.get("mode", "closed_book")

    plan = planner.invoke(
        [
            SystemMessage(content=ORCH_SYSTEM),
            HumanMessage(
                content=(
                    f"Topic: {state['topic']}\n"
                    f"Mode: {mode}\n\n"
                    f"Evidence (ONLY use for fresh claims; may be empty):\n"
                    # Send max 6 evidence items to keep context lean
                    f"{[e.model_dump() for e in evidence][:6]}"
                )
            ),
        ]
    )

    return {"plan": plan}
