"""The quiz agent: answers multiple-choice questions with a single letter.

Plain Haystack. An `Agent` is a chat model in a loop: it reads the question, may call a tool,
reads the result, and answers. Make it faster and cheaper -- but keep it right.

Two things the platform cares about:
- A bare `Agent` deploys as-is: the CLI wraps it in a one-component pipeline called `agent`.
- The OpenAI key is never in this file. It serializes as an env-var reference that the platform
  fills in from your workspace, so you need no key of your own.

Tuned with evals/run_eval.py (60 questions, see evals/): no tools and a brief hidden reasoning
pass beat the calculator/letter tools on both accuracy (60/60 vs 59/60) and tokens (~70 vs ~460
per question). Tool schemas are paid on every call and each tool call is another round trip,
while low reasoning effort spends tokens only on the questions that need them.
"""

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.utils import Secret

MODEL = "gpt-5.4"

# Shortest prompt that kept the format perfect; "Letter only." sometimes got "C) Carbon dioxide".
SYSTEM_PROMPT = "Reply with only the correct option letter."

agent = Agent(
    # strict=False: the key only has to exist on the platform, not on your machine.
    chat_generator=OpenAIChatGenerator(
        model=MODEL,
        api_key=Secret.from_env_var("OPENAI_API_KEY", strict=False),
        # Low reasoning: ~0 thinking tokens on trivia, a few dozen on arithmetic and letter counts.
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
)
