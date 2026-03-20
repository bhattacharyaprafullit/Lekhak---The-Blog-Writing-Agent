"""
ui/tabs/logs_tab.py
-------------------
Renders the "Logs" tab: a scrollable text area showing the raw LangGraph
stream events. Useful for debugging which node ran, what state looked like
after each step, and why something went wrong.

We only show the last 80 log entries to keep the text area manageable.
"""

from typing import List

import streamlit as st


def render_logs_tab(fresh_logs: List[str]) -> None:
    st.subheader("Logs")

    # Merge any new logs from the current run into the persistent session log
    if fresh_logs:
        st.session_state["logs"].extend(fresh_logs)

    st.text_area(
        "Event log",
        value="\n\n".join(st.session_state["logs"][-80:]),
        height=520,
    )
