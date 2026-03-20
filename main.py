"""
main.py
-------
The Streamlit entry point. This file should stay thin — its only job is to
wire together the sidebar, the graph runner, and the tabs.

Run with:
    streamlit run main.py

Architecture summary
--------------------
main.py
  └── ui/sidebar.py          (topic input + past-blog management)
  └── app/graph/builder.py   (compiled LangGraph app)
  └── ui/tabs/
        plan_tab.py
        evidence_tab.py
        preview_tab.py
        social_tab.py
        logs_tab.py
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

import streamlit as st

from app.graph.builder import app
from ui.sidebar import render_sidebar
from ui.tabs.plan_tab import render_plan_tab
from ui.tabs.evidence_tab import render_evidence_tab
from ui.tabs.preview_tab import render_preview_tab
from ui.tabs.social_tab import render_social_tab
from ui.tabs.logs_tab import render_logs_tab

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Lekhak AI", layout="wide")

# Logo in the main area instead of a plain text title
MAIN_LOGO_SVG = """
<svg width="100%" viewBox="0 0 680 160" xmlns="http://www.w3.org/2000/svg">
  <rect x="0" y="0" width="680" height="160" fill="#111213" rx="10"/>
  <text x="155" y="100"
        text-anchor="end"
        font-family="'Noto Sans Devanagari', 'Mangal', serif"
        font-size="62" font-weight="700" fill="#e63329">&#2354;&#2375;&#2326;&#2325;</text>
  <text x="172" y="100"
        font-family="Georgia, 'Times New Roman', serif"
        font-size="62" font-weight="700" fill="#ffffff">AI</text>
  <rect x="28" y="114" width="232" height="3" fill="#e63329" rx="2"/>
  <text x="28" y="145"
        font-family="Arial, Helvetica, sans-serif"
        font-size="12" font-weight="400"
        fill="#666666" letter-spacing="3">YOUR SMART BLOG AGENT</text>
</svg>
"""
st.markdown(MAIN_LOGO_SVG, unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)
# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------
if "last_out" not in st.session_state:
    st.session_state["last_out"] = None

if "logs" not in st.session_state:
    st.session_state["logs"] = []

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
topic, run_btn = render_sidebar()

# ---------------------------------------------------------------------------
# Tab shell (always rendered so tabs don't flash in/out)
# ---------------------------------------------------------------------------
tab_plan, tab_evidence, tab_preview, tab_social, tab_logs = st.tabs(
    ["Plan", "Evidence", "Markdown Preview", "Social Media", "Logs"]
)

# ---------------------------------------------------------------------------
# Stream helpers (copied from original — logic unchanged)
# ---------------------------------------------------------------------------

def _try_stream(graph_app, inputs):
    """
    Attempt streaming first; fall back to a single invoke() call if streaming
    raises an exception. This keeps the UI working even in environments where
    streaming is not supported.
    """
    try:
        final_state: Dict[str, Any] = {}
        for step in graph_app.stream(inputs, stream_mode="updates"):
            yield ("updates", step)
            if isinstance(step, dict):
                for v in step.values():
                    if isinstance(v, dict):
                        final_state.update(v)
        yield ("final", final_state)
        return
    except Exception:
        pass

    # Fallback
    out = graph_app.invoke(inputs)
    yield ("final", out)


def _extract_latest_state(
    current_state: Dict[str, Any], step_payload: Any
) -> Dict[str, Any]:
    """Merge a single stream step payload into the running state dict."""
    if isinstance(step_payload, dict):
        if len(step_payload) == 1 and isinstance(
            next(iter(step_payload.values())), dict
        ):
            inner = next(iter(step_payload.values()))
            current_state.update(inner)
        else:
            current_state.update(step_payload)
    return current_state


# ---------------------------------------------------------------------------
# Graph execution (only runs when the user clicks Generate)
# ---------------------------------------------------------------------------
fresh_logs: List[str] = []

if run_btn:
    if not topic.strip():
        st.warning("Please enter a topic.")
        st.stop()

    inputs: Dict[str, Any] = {
        "topic": topic.strip(),
        "mode": "",
        "needs_research": False,
        "queries": [],
        "evidence": [],
        "plan": None,
        "sections": [],
        "final": "",
        "social_media": {},
    }

    status = st.status("Running...", expanded=True)
    progress_area = st.empty()

    current_state: Dict[str, Any] = {}
    last_node = None

    for kind, payload in _try_stream(app, inputs):
        if kind in ("updates", "values"):
            # Show which node is currently active
            node_name = None
            if isinstance(payload, dict) and len(payload) == 1:
                node_name = next(iter(payload.keys()))
            if node_name and node_name != last_node:
                status.write(f"Node: `{node_name}`")
                last_node = node_name

            current_state = _extract_latest_state(current_state, payload)

            # Live progress summary
            summary = {
                "mode": current_state.get("mode"),
                "needs_research": current_state.get("needs_research"),
                "evidence_count": len(current_state.get("evidence", []) or []),
                "sections_done": len(current_state.get("sections", []) or []),
            }
            progress_area.json(summary)
            fresh_logs.append(f"[{kind}] {json.dumps(payload, default=str)[:1200]}")

        elif kind == "final":
            st.session_state["last_out"] = payload
            st.session_state["logs"].extend(fresh_logs)
            status.update(label="Done!", state="complete", expanded=False)
            fresh_logs.append("[final] received final state")

# ---------------------------------------------------------------------------
# Render tabs (always attempts to render if there is output in session state)
# ---------------------------------------------------------------------------
out = st.session_state.get("last_out")

if out:
    with tab_plan:
        render_plan_tab(out)

    with tab_evidence:
        render_evidence_tab(out)

    with tab_preview:
        render_preview_tab(out)

    with tab_social:
        render_social_tab(out)

    with tab_logs:
        render_logs_tab(fresh_logs)

else:
    with tab_preview:
        st.info("Enter a topic and click Generate Blog.")
