# Blog Writing Agent

An AI-powered blog writing agent built with LangGraph, LangChain, and Streamlit.
The agent plans, researches (when needed), writes, and distributes a full blog post
from a single topic prompt — in parallel, with social media content included.

---

## Architecture

```
blog_writing_agent/
│
├── app/                        # Pure Python — no Streamlit anywhere in here
│   ├── models/
│   │   └── schemas.py          # All Pydantic models + TypedDict State
│   ├── core/
│   │   └── llm.py              # LLM client (swap Groq → OpenAI here only)
│   ├── nodes/
│   │   ├── router.py           # Decides research mode before planning
│   │   ├── research.py         # Tavily search + evidence synthesis
│   │   ├── orchestrator.py     # Produces the structured blog Plan
│   │   ├── worker.py           # Writes one section (runs in parallel)
│   │   ├── reducer.py          # Merges parallel sections + saves .md
│   │   └── social_media.py     # Twitter thread, LinkedIn, newsletter
│   ├── graph/
│   │   └── builder.py          # Wires all nodes into a LangGraph StateGraph
│   └── utils/
│       └── file_utils.py       # Filesystem helpers (slug, read, list, extract)
│
├── ui/                         # Streamlit layer — imports from app/, never vice versa
│   ├── sidebar.py              # Topic input + past-blog list with load/delete
│   └── tabs/
│       ├── plan_tab.py
│       ├── evidence_tab.py
│       ├── preview_tab.py
│       ├── social_tab.py
│       └── logs_tab.py
│
├── main.py                     # Entry point: wires sidebar + graph + tabs
├── .env                        # API keys (never commit this)
├── requirements.txt
└── README.md
```

### Key design decisions

**Strict layer separation.** The `app/` package contains zero Streamlit code.
This means you can run the agent headlessly (e.g. via `app.graph.builder.app.invoke(...)`)
without Streamlit being installed.

**One responsibility per file.** Each node file owns its system prompt *and*
its node function. Reading `worker.py` tells you everything about how a section
gets written — no jumping between files.

**Single coupling point.** `graph/builder.py` is the only file that knows how
nodes connect. Adding a new step (e.g. a fact-checker) means editing exactly
one file.

**Testable utilities.** `app/utils/file_utils.py` has no imports beyond the
standard library. You can unit-test it with plain `pytest` — no LangGraph,
no LLM, no mocking needed.

---

## Quickstart

```bash
# 1. Clone / download the project
cd blog_writing_agent

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys
cp .env.example .env
# Then edit .env with your actual keys

# 5. Run
streamlit run main.py
```

---

## Environment variables

Create a `.env` file in the project root:

```
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key   # only needed for hybrid/open_book topics
```

---

## How the graph works

```
START
  └── router         (decides: closed_book / hybrid / open_book)
        ├── [needs_research=False] ──────────────────┐
        └── [needs_research=True] → research ─────────┤
                                                       ▼
                                               orchestrator  (builds Plan)
                                                       │
                                          fanout (one Send per Task)
                                                       │
                                           ┌───────────┴───────────┐
                                         worker                  worker   ...
                                           └───────────┬───────────┘
                                                       ▼
                                                   reducer  (sorts + saves .md)
                                                       │
                                                social_media
                                                       │
                                                      END
```

The worker fan-out is the key performance win: all N sections are written
in parallel, then the reducer re-orders them by task ID.

---

## Extending the project

To add a new node (e.g. an SEO scorer):

1. Create `app/nodes/seo_scorer.py` with the node function and its system prompt.
2. In `app/graph/builder.py`, `add_node("seo_scorer", seo_scorer_node)` and wire
   the appropriate edges.
3. If it produces UI output, add `ui/tabs/seo_tab.py` and register the tab in `main.py`.

Nothing else needs to change.
