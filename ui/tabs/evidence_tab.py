"""
ui/tabs/evidence_tab.py
-----------------------
Renders the "Evidence" tab: shows research sources found by the research node.
Only populated when the router chose hybrid or open_book mode.
"""

import pandas as pd
import streamlit as st


def render_evidence_tab(out: dict) -> None:
    st.subheader("Evidence")
    evidence = out.get("evidence") or []

    if not evidence:
        st.info("No evidence (closed_book mode or no Tavily results).")
        return

    rows = []
    for e in evidence:
        if hasattr(e, "model_dump"):
            e = e.model_dump()
        rows.append(
            {
                "title": e.get("title"),
                "published_at": e.get("published_at"),
                "source": e.get("source"),
                "url": e.get("url"),
            }
        )

    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
