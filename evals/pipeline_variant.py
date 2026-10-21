"""agent.py's pipeline (QuickAnswer -> Agent -> BranchJoiner), configurable through env vars.

QZ_MODEL, QZ_PROMPT (empty = no system prompt), QZ_KWARGS (JSON generation_kwargs).
Used to compare models in the exact pipeline that is deployed, e.g. the gpt-5.6-luna fork.
"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from haystack import Pipeline
from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.joiners import BranchJoiner
from haystack.dataclasses import ChatMessage
from haystack.utils import Secret

from quick_answer import QuickAnswer

kwargs = {"stream_options": {"include_usage": True}}
kwargs.update(json.loads(os.environ.get("QZ_KWARGS", "{}")))

pipeline = Pipeline()
pipeline.add_component("quick", QuickAnswer())
pipeline.add_component(
    "agent",
    Agent(
        chat_generator=OpenAIChatGenerator(
            model=os.environ["QZ_MODEL"],
            api_key=Secret.from_env_var("OPENAI_API_KEY", strict=False),
            generation_kwargs=kwargs,
        ),
        system_prompt=os.environ.get("QZ_PROMPT") or None,
        max_agent_steps=1,
    ),
)
pipeline.add_component("joiner", BranchJoiner(list[ChatMessage]))
pipeline.connect("quick.unanswered", "agent.messages")
pipeline.connect("quick.answered", "joiner.value")
pipeline.connect("agent.messages", "joiner.value")
