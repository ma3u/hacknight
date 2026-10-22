"""The quiz agent: answers multiple-choice questions with a single letter.

A Haystack pipeline built from stock parts plus one small custom component:

    messages -> QuickAnswer --answered-------------------------------------------------> BranchJoiner -> messages
                    \\--unanswered--> ConditionalRouter --recent--> Agent + web search ---/
                                                         \\--timeless-> Agent ----------/

- QuickAnswer solves letter counts and plain arithmetic in Python: zero tokens, milliseconds.
- ConditionalRouter sends questions about recent events (2025/2026, latest, current, new) to an agent with
  OpenAI's built-in web search (Responses API): the live quiz asked about events no model can know.
- Everything else goes to the plain agent: no tools, low reasoning, ~50-75 tokens per question.
The OpenAI key is never in this file: it serializes as an env-var reference that the platform fills in.

Tuned with evals/run_eval.py (see evals/RESULTS.md). Recent events: 4/14 without search, 14/14 with it
(~9k tokens, ~7 s each, so only routed questions search). Timeless questions are unchanged (174/174 overall).
"""

from haystack import Pipeline
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIResponsesChatGenerator
from haystack.components.joiners import BranchJoiner
from haystack.components.routers import ConditionalRouter
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret

from quick_answer import QuickAnswer

MODEL = "gpt-5.4-mini"

# Shortest prompt that kept the format perfect; "Letter only." sometimes got "C) Carbon dioxide".
# "If unsure, guess.": without it a model may answer "I don't know", which scores like a wrong letter.
SYSTEM_PROMPT = "Reply with only the correct option letter. If unsure, guess."

# Recent = the question line (not the options) mentions 2025/2026 or latest/current/new.
# Lowercase "new" only: "deepset's new office" is recent, "New Zealand" / "New York" are not.
RECENT = ("{% set line = (messages[-1].text or '').split('\\n') | first %}{% set q = line | lower %}"
          "{{ '2025' in q or '2026' in q or 'latest' in q or 'current' in q or 'recent' in q "
          "or ' new ' in line or 'newest' in q }}")
ROUTES = [
    {"condition": RECENT, "output": "{{ messages }}", "output_name": "recent", "output_type": list[ChatMessage]},
    {"condition": "{{ true }}", "output": "{{ messages }}", "output_name": "timeless", "output_type": list[ChatMessage]},
]


def build_pipeline(model: str) -> Pipeline:
    """The quiz pipeline for one model; agent_luna.py reuses it with gpt-5.6-luna."""
    # strict=False: the key only has to exist on the platform, not on your machine.
    api_key = Secret.from_env_var("OPENAI_API_KEY", strict=False)
    pipeline = Pipeline()
    pipeline.add_component("quick", QuickAnswer())
    # unsafe=True keeps ChatMessage objects (safe mode renders them to strings); the templates are ours.
    pipeline.add_component("router", ConditionalRouter(routes=ROUTES, unsafe=True))
    pipeline.add_component(
        "agent",
        Agent(
            # Responses API for both agents: with two agents the platform streams only one of them, and
            # Responses reports token usage either way (Chat Completions needs stream_options, which a
            # non-streamed call rejects). max_output_tokens is only a cap; usage counts what is spent.
            chat_generator=OpenAIResponsesChatGenerator(
                model=model,
                api_key=api_key,
                generation_kwargs={"reasoning_effort": "low", "max_output_tokens": 1000},
            ),
            system_prompt=SYSTEM_PROMPT,
            max_agent_steps=1,
        ),
    )
    pipeline.add_component(
        "web_agent",
        Agent(
            # OpenAI's hosted web search runs on the same OpenAI key, inside one Responses API call.
            chat_generator=OpenAIResponsesChatGenerator(
                model=model,
                api_key=api_key,
                # Low search context: same 14/14 on recent events, slowest answer 10 s instead of 16 s.
                tools=[{"type": "web_search", "search_context_size": "low"}],
                generation_kwargs={"reasoning_effort": "low", "max_output_tokens": 2000},
            ),
            system_prompt=SYSTEM_PROMPT,
            max_agent_steps=1,
        ),
    )
    pipeline.add_component("joiner", BranchJoiner(list[ChatMessage]))
    pipeline.connect("quick.unanswered", "router.messages")
    pipeline.connect("router.recent", "web_agent.messages")
    pipeline.connect("router.timeless", "agent.messages")
    pipeline.connect("quick.answered", "joiner.value")
    pipeline.connect("agent.messages", "joiner.value")
    pipeline.connect("web_agent.messages", "joiner.value")
    return pipeline


pipeline = build_pipeline(MODEL)
