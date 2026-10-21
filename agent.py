"""The quiz agent: answers multiple-choice questions with a single letter.

A Haystack pipeline built from stock parts plus one small custom component:

    messages -> QuickAnswer --answered-----------------------> BranchJoiner -> messages
                    \--unanswered--> Agent (gpt-5.4) --------/

QuickAnswer solves letter counts and plain arithmetic in Python: zero tokens, milliseconds.
Everything else goes to the Agent. The OpenAI key is never in this file: it serializes as an
env-var reference that the platform fills in from your workspace.

Tuned with evals/run_eval.py (60 questions, see evals/). Agent alone with no tools and low
reasoning: 60/60 at ~70 tokens per question, vs 59/60 at ~460 for the starter agent with tools.
Low reasoning costs nothing extra on trivia (same tokens as "none"); it only thinks on
questions that need it, which are mostly the ones QuickAnswer now takes over.
"""

from haystack import Pipeline
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.joiners import BranchJoiner
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret

from quick_answer import QuickAnswer

MODEL = "gpt-5.4-mini"

# Shortest prompt that kept the format perfect; "Letter only." sometimes got "C) Carbon dioxide".
SYSTEM_PROMPT = "Reply with only the correct option letter."


def build_pipeline(model: str) -> Pipeline:
    """The quiz pipeline for one model; agent_luna.py reuses it with gpt-5.6-luna."""
    pipeline = Pipeline()
    pipeline.add_component("quick", QuickAnswer())
    pipeline.add_component(
        "agent",
        Agent(
            # strict=False: the key only has to exist on the platform, not on your machine.
            chat_generator=OpenAIChatGenerator(
                model=model,
                api_key=Secret.from_env_var("OPENAI_API_KEY", strict=False),
                # max_completion_tokens is only a cap (it includes reasoning); usage counts what is spent.
                # include_usage: the platform streams, and a stream only reports token usage when asked.
                generation_kwargs={
                    "reasoning_effort": "low",
                    "max_completion_tokens": 1000,
                    "stream_options": {"include_usage": True},
                },
            ),
            system_prompt=SYSTEM_PROMPT,
            max_agent_steps=1,
        ),
    )
    pipeline.add_component("joiner", BranchJoiner(list[ChatMessage]))
    pipeline.connect("quick.unanswered", "agent.messages")
    pipeline.connect("quick.answered", "joiner.value")
    pipeline.connect("agent.messages", "joiner.value")
    return pipeline


pipeline = build_pipeline(MODEL)
