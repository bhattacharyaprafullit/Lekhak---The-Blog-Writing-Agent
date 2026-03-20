"""
ui/tabs/plan_tab.py
-------------------
Renders the "Plan" tab: shows blog metadata and the task table.
"""

import json

import pandas as pd
import streamlit as st


def render_plan_tab(out: dict) -> None:
    st.subheader("Plan")
    plan_obj = out.get("plan")

    if not plan_obj:
        st.info("No plan found.")
        return

    # Normalise to dict regardless of whether plan is a Pydantic object or raw dict
    if hasattr(plan_obj, "model_dump"):
        plan_dict = plan_obj.model_dump()
    elif isinstance(plan_obj, dict):
        plan_dict = plan_obj
    else:
        plan_dict = json.loads(json.dumps(plan_obj, default=str))

    st.write("**Title:**", plan_dict.get("blog_title"))

    cols = st.columns(3)
    cols[0].write("**Audience:** " + str(plan_dict.get("audience")))
    cols[1].write("**Tone:** " + str(plan_dict.get("tone")))
    cols[2].write("**Blog kind:** " + str(plan_dict.get("blog_kind", "")))

    tasks = plan_dict.get("tasks", [])
    if tasks:
        df = pd.DataFrame(
            [
                {
                    "id": t.get("id"),
                    "title": t.get("title"),
                    "target_words": t.get("target_words"),
                    "requires_research": t.get("requires_research"),
                    "requires_citations": t.get("requires_citations"),
                    "requires_code": t.get("requires_code"),
                    "tags": ", ".join(t.get("tags") or []),
                }
                for t in tasks
            ]
        ).sort_values("id")

        st.dataframe(df, use_container_width=True, hide_index=True)

        with st.expander("Task details"):
            st.json(tasks)
