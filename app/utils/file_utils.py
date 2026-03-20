"""
utils/file_utils.py
-------------------
Pure filesystem helpers — no Streamlit, no LangGraph, no LLM.

Keeping these here means:
- They're testable in isolation (just call the functions, no UI needed).
- The UI layer imports them without pulling in any heavy dependencies.
- If you add a FastAPI layer later, it can reuse the same helpers.
"""

import re
from pathlib import Path
from typing import List


def safe_slug(title: str) -> str:
    """
    Convert a blog title to a safe filename slug.
    e.g. "How RAG Works: A Deep Dive" -> "how_rag_works_a_deep_dive"
    """
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9 _-]+", "", s)
    s = re.sub(r"\s+", "_", s).strip("_")
    return s or "blog"


def read_md_file(p: Path) -> str:
    """Read a Markdown file, replacing undecodable bytes gracefully."""
    return p.read_text(encoding="utf-8", errors="replace")


def extract_title_from_md(md: str, fallback: str) -> str:
    """
    Pull the H1 title out of a Markdown string.
    Returns `fallback` if no '# ...' line is found.
    """
    for line in md.splitlines():
        if line.startswith("# "):
            t = line[2:].strip()
            return t or fallback
    return fallback


def list_past_blogs(search_query: str = "") -> List[Path]:
    """
    Find all .md files in the current working directory, newest first.
    If `search_query` is provided, only return files whose extracted title
    contains the query string (case-insensitive).
    """
    cwd = Path(".")
    files = [p for p in cwd.glob("*.md") if p.is_file()]

    if search_query.strip():
        filtered = []
        for p in files:
            try:
                md_text = read_md_file(p)
                title = extract_title_from_md(md_text, p.stem)
                if search_query.lower() in title.lower():
                    filtered.append(p)
            except Exception:
                pass
        files = filtered

    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return files
