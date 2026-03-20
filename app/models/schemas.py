"""
schemas.py
----------
All Pydantic models and TypedDict state definitions for the Blog Writing Agent.
Keeping these in one place means a single source of truth for your data shapes.
"""

from __future__ import annotations

import operator
from typing import TypedDict, List, Annotated, Literal, Optional

from pydantic import BaseModel, Field, field_validator


class Task(BaseModel):
    id: int
    title: str
    goal: str = Field(
        ...,
        description="One sentence describing what the reader should be able to do/understand after this section.",
    )
    bullets: List[str] = Field(
        ...,
        min_length=3,
        max_length=4,
        description="3–4 concrete, non-overlapping subpoints to cover in this section.",
    )
    target_words: int = Field(..., description="Target word count for this section (120–300).")
    tags: List[str] = Field(default_factory=list)
    requires_research: bool = False
    requires_citations: bool = False
    requires_code: bool = False


class Plan(BaseModel):
    blog_title: str
    audience: str
    tone: str
    blog_kind: Literal["explainer", "tutorial", "news_roundup", "comparison", "system_design"] = "explainer"
    constraints: List[str] = Field(default_factory=list)
    tasks: List[Task]


class EvidenceItem(BaseModel):
    title: str
    url: str
    published_at: Optional[str] = None
    snippet: Optional[str] = None
    source: Optional[str] = None


class RouterDecision(BaseModel):
    needs_research: bool
    mode: Literal["closed_book", "hybrid", "open_book"]
    queries: List[str] = Field(default_factory=list)

    @field_validator("needs_research", mode="before")
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, str):
            return v.lower() == "true"
        return v


class EvidencePack(BaseModel):
    evidence: List[EvidenceItem] = Field(default_factory=list)


class SocialMediaContent(BaseModel):
    twitter_thread: List[str] = Field(
        default_factory=list,
        description="6 tweets, each under 280 characters, with emojis"
    )
    linkedin_post: str = Field(
        default="",
        description="Engaging LinkedIn post 800-1200 characters with emojis and hashtags"
    )
    newsletter: str = Field(
        default="",
        description="Email newsletter 400-600 characters with subject line and CTA"
    )


class State(TypedDict):
    topic: str

    # routing / research
    mode: str
    needs_research: bool
    queries: List[str]
    evidence: List[EvidenceItem]
    plan: Optional[Plan]

    # workers
    sections: Annotated[List[tuple[int, str]], operator.add]   # (task_id, section_md)
    social_media: dict
    final: str
    output_path: str
