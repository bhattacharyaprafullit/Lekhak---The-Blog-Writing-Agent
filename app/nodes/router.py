"""
nodes/router.py
---------------
The Router node decides BEFORE any writing happens whether web research is needed.

Three possible outcomes:
- closed_book  : Evergreen topic, no search needed (e.g., "explain recursion").
- hybrid       : Mostly evergreen but benefits from fresh examples/tools.
- open_book    : Highly volatile — weekly roundups, "latest X", pricing, policy.

This node updates the state with mode, needs_research, and search queries.
"""

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm import llm
from app.models.schemas import RouterDecision, State

ROUTER_SYSTEM = """You are a routing module for a technical blog planner.

Decide whether web research is needed BEFORE planning.
Respond in JSON format.

Modes:
- closed_book (needs_research=false):
  Evergreen topics where correctness does not depend on recent facts (concepts, fundamentals).
- hybrid (needs_research=true):
  Mostly evergreen but needs up-to-date examples/tools/models to be useful.
- open_book (needs_research=true):
  Mostly volatile: weekly roundups, "this week", "latest", rankings, pricing, policy/regulation.

If needs_research=true:
- Output 3-5 high-signal queries only.
- Queries should be scoped and specific.
"""


def router_node(state: State) -> dict:
    topic = state["topic"]
    decider = llm.with_structured_output(RouterDecision, method="json_mode")
    decision = decider.invoke(
        [
            SystemMessage(content=ROUTER_SYSTEM),
            HumanMessage(content=f"Topic: {topic}"),
        ]
    )
    return {
        "needs_research": decision.needs_research,
        "mode": decision.mode,
        "queries": decision.queries,
    }


def route_next(state: State) -> str:
    """Conditional edge: go to research if needed, else straight to orchestrator."""
    return "research" if state["needs_research"] else "orchestrator"
