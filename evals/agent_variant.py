"""agent.py, configurable through env vars, so the eval runner can try many variants.

QZ_MODEL, QZ_PROMPT, QZ_TOOLS ("calculate,count_letter" or ""), QZ_KWARGS (JSON), QZ_STEPS.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.utils import Secret

from calculator import calculate
from letters import count_letter

TOOLS = {"calculate": calculate, "count_letter": count_letter}

kwargs = {"stream_options": {"include_usage": True}}
kwargs.update(json.loads(os.environ.get("QZ_KWARGS", "{}")))
tools = [TOOLS[t] for t in os.environ.get("QZ_TOOLS", "").split(",") if t]

agent = Agent(
    chat_generator=OpenAIChatGenerator(
        model=os.environ["QZ_MODEL"],
        api_key=Secret.from_env_var("OPENAI_API_KEY", strict=False),
        generation_kwargs=kwargs,
    ),
    tools=tools or None,
    system_prompt=os.environ.get("QZ_PROMPT") or None,
    max_agent_steps=int(os.environ.get("QZ_STEPS", "3")),
)
