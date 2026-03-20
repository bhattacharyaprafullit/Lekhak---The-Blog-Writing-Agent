"""
ui/sidebar.py
-------------
Everything that lives in the Streamlit sidebar.

Why a separate file?
- The sidebar has its own state concerns (which blog is selected, search query).
- Keeping it here means main.py stays thin — it just calls render_sidebar()
  and gets back two things: the topic the user typed, and whether they clicked
  Generate.
- The "past blogs" list and file operations are UI concerns; they use file_utils
  but don't touch the LangGraph app at all.
"""

from pathlib import Path
from typing import Optional, Tuple

import streamlit as st

from app.utils.file_utils import list_past_blogs, read_md_file, extract_title_from_md


def render_sidebar() -> Tuple[str, bool]:
    """
    Render the full sidebar and return (topic, should_generate).

    Returns:
        topic          : The text the user entered in the topic box.
        should_generate: True if the user clicked the Generate button.

    Side-effects:
        - May update st.session_state["last_out"] if the user loads a past blog.
        - May delete a file and call st.rerun() if the user clicks Delete.
    """
    with st.sidebar:
        st.header("Generate New Blog")
        topic = st.text_area("Topic", height=120)
        run_btn = st.button("Generate Blog", type="primary")

        st.divider()
        st.subheader("Past Blogs")

        search_query = st.text_input("Search blogs", placeholder="Type title to search...")

        past_files = list_past_blogs(search_query)

        if not past_files:
            caption = "No saved blogs found." if not search_query else f"No blogs found for '{search_query}'"
            st.caption(caption)
        else:
            _render_past_blogs_list(past_files)

    return topic, run_btn


def _render_past_blogs_list(past_files: list) -> None:
    """Internal helper: radio list + Load/Delete buttons for past blogs."""
    from typing import Dict

    options = []
    file_by_label: Dict[str, Path] = {}

    for p in past_files[:50]:
        try:
            md_text = read_md_file(p)
            title = extract_title_from_md(md_text, p.stem)
        except Exception:
            title = p.stem
        label = f"{title}  ·  {p.name}"
        options.append(label)
        file_by_label[label] = p

    selected_label = st.radio(
        "Select a blog to load",
        options=options,
        index=0,
        label_visibility="collapsed",
    )
    selected_md_file: Optional[Path] = file_by_label.get(selected_label)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Load Blog", use_container_width=True):
            if selected_md_file:
                md_text = read_md_file(selected_md_file)
                st.session_state["last_out"] = {
                    "plan": None,
                    "evidence": [],
                    "social_media": {},
                    "final": md_text,
                }
                st.rerun()

    with col2:
        if st.button("Delete", type="secondary", use_container_width=True):
            if selected_md_file and selected_md_file.exists():
                selected_md_file.unlink()
                st.success("Deleted!")
                st.rerun()
