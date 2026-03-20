"""
graph/builder.py
----------------
This is the ONLY file that knows how nodes connect to each other.

The key design principle: builder.py imports nodes but nodes do NOT import
each other. All coupling lives here. If you want to add a new node (e.g., a
"fact-checker" step after the reducer), you add it here without touching
any other node file.

Fan-out pattern:
  The orchestrator produces a Plan with N tasks. The `fanout` function uses
  LangGraph's Send API to dispatch each task to a separate "worker" invocation
  running in parallel. Workers write back to state["sections"] via the
  Annotated[List, operator.add] reducer, which merges all parallel results.
  The reducer_node then sorts and assembles the final document.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.types import Send

from app.models.schemas import State
from app.nodes.router import router_node, route_next
from app.nodes.research import research_node
from app.nodes.orchestrator import orchestrator_node
from app.nodes.worker import worker_node
from app.nodes.reducer import reducer_node
from app.nodes.social_media import social_media_node


def fanout(state: State):
    """
    Conditional edge after orchestrator: spawns one worker per Task.
    Each Send call delivers a self-contained payload so the worker does not
    need access to the full State (important for parallel safety).
    """
    return [
        Send(
            "worker",
            {
                "task": task.model_dump(),
                "topic": state["topic"],
                "mode": state["mode"],
                "plan": state["plan"].model_dump(),
                "evidence": [e.model_dump() for e in state.get("evidence", [])],
            },
        )
        for task in state["plan"].tasks
    ]


def build_graph():
    """Assemble and compile the LangGraph StateGraph. Returns the compiled app."""
    g = StateGraph(State)

    # Register nodes
    g.add_node("router", router_node)
    g.add_node("research", research_node)
    g.add_node("orchestrator", orchestrator_node)
    g.add_node("worker", worker_node)
    g.add_node("reducer", reducer_node)
    g.add_node("social_media", social_media_node)

    # Wire edges
    g.add_edge(START, "router")
    g.add_conditional_edges(
        "router",
        route_next,
        {"research": "research", "orchestrator": "orchestrator"},
    )
    g.add_edge("research", "orchestrator")
    g.add_conditional_edges("orchestrator", fanout, ["worker"])
    g.add_edge("worker", "reducer")
    g.add_edge("reducer", "social_media")
    g.add_edge("social_media", END)

    return g.compile()


# Module-level compiled app — import this wherever you need to run the graph.
app = build_graph()
