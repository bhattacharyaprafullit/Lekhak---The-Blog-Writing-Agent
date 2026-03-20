"""
core/llm.py
-----------
Centralised LLM client initialisation.

Why isolate this?
- If you ever swap Groq for OpenAI / Anthropic / Ollama, this is the ONLY file
  you need to touch. Every node imports `llm` from here.
- Environment variables are loaded once here via dotenv.
"""

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# Single shared LLM instance used by all nodes.
# All structured-output calls use method="json_mode" so the model always
# returns parseable JSON — this is set per-call in each node.
llm = ChatGroq(model="llama-3.3-70b-versatile")
