"""
nodes/reducer.py
----------------
The Reducer node collects all (task_id, section_md) tuples that workers
deposited into state["sections"], sorts them by task_id to restore the
correct reading order, and assembles the final Markdown document.

It also persists the file to disk. The output directory is always the
folder containing this project (resolved via Path.cwd()), so the saved
.md file sits alongside your source files — exactly where you'd expect it.
"""

from pathlib import Path

from app.models.schemas import State


def reducer_node(state: State) -> dict:
    plan = state["plan"]

    # Sort by task_id so sections appear in the planned order,
    # regardless of which worker finished first (parallel execution).
    ordered_sections = [
        md for _, md in sorted(state["sections"], key=lambda x: x[0])
    ]
    body = "\n\n".join(ordered_sections).strip()
    final_md = f"# {plan.blog_title}\n\n{body}\n"

    # Build a safe filename: keep only alphanumerics, spaces, hyphens, underscores.
    safe_title = "".join(
        c for c in plan.blog_title if c.isalnum() or c in (" ", "-", "_")
    ).strip()

    output_dir = Path.cwd()
    output_dir.mkdir(parents=True, exist_ok=True)

    filename = output_dir / f"{safe_title}.md"
    filename.write_text(final_md, encoding="utf-8")
    print(f"Saved to: {filename}")

    return {"final": final_md, "output_path": str(filename)}
