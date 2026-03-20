"""
ui/tabs/preview_tab.py
----------------------
Renders the "Markdown Preview" tab: shows the rendered blog, a download button,
and an inline editor so the user can make quick fixes without leaving the app.
"""

from pathlib import Path

import streamlit as st

from app.utils.file_utils import safe_slug, extract_title_from_md


def render_preview_tab(out: dict) -> None:
    st.subheader("Markdown Preview")
    final_md = out.get("final") or ""

    if not final_md:
        st.warning("No final markdown found.")
        return

    st.markdown(final_md, unsafe_allow_html=False)

    # Resolve the blog title for the download filename
    plan_obj = out.get("plan")
    if hasattr(plan_obj, "blog_title"):
        blog_title = plan_obj.blog_title
    elif isinstance(plan_obj, dict):
        blog_title = plan_obj.get("blog_title", "blog")
    else:
        blog_title = extract_title_from_md(final_md, "blog")

    md_filename = f"{safe_slug(blog_title)}.md"

    st.download_button(
        "Download Markdown",
        data=final_md.encode("utf-8"),
        file_name=md_filename,
        mime="text/markdown",
    )

    st.divider()

    with st.expander("Edit Blog"):
        edited_md = st.text_area(
            "Edit your blog here",
            value=final_md,
            height=400,
            key="edit_blog_area",
        )
        if st.button("Save Changes"):
            filepath = Path.cwd() / md_filename
            filepath.write_text(edited_md, encoding="utf-8")
            # Keep session state in sync with the saved file
            st.session_state["last_out"]["final"] = edited_md
            st.success("Blog saved successfully!")
            st.rerun()
