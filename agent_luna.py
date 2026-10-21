"""The quiz pipeline with gpt-5.6-luna, deployed as service `quiz-luna`.

Fixes the platform fork quiz-cf5ea67e-fork, which kept the pipeline but dropped the agent's
system prompt and generation_kwargs: without "Reply with only the correct option letter." Luna
answered "D) Inception" instead of "D", which the quiz scores as wrong, and without
include_usage the streamed answers reported no token usage.

Deploy: haystack-enterprise deploy agent_luna.py quiz-luna --io-config agent.io.yaml
"""

from agent import build_pipeline

MODEL = "gpt-5.6-luna"

pipeline = build_pipeline(MODEL)
