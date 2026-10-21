"""Run agent variants over evals/questions.json in the platform sandbox.

uv run python evals/run_eval.py VARIANT [VARIANT ...]   (names from VARIANTS below)
Prints accuracy, total tokens and latency per variant; saves details to evals/results/.
"""

import json
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from check import format_question, last_reply, tokens_used  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
QUESTIONS = json.loads((HERE / os.environ.get("QZ_SET", "questions.json")).read_text())
if os.environ.get("QZ_SAMPLE"):  # fixed random subset, identical for every variant
    QUESTIONS = random.Random(7).sample(QUESTIONS, int(os.environ["QZ_SAMPLE"]))

BASE_PROMPT = (
    "You answer multiple-choice quiz questions. Each question has options A, B, C and D. "
    "Use the calculate tool for any arithmetic. "
    "Use count_letter only when the question asks how many times a letter appears in a word. "
    "Reply with ONLY the letter of the correct option: A, B, C or D. No other text."
)
SHORT_PROMPT = "Reply with only the correct option letter."
NO_REASON = {"reasoning_effort": "none", "max_completion_tokens": 50}

VARIANTS = {
    # v0: the harness as shipped
    "v0_baseline_gpt51": dict(model="gpt-5.1", prompt=BASE_PROMPT, tools="calculate,count_letter", kwargs=NO_REASON),
    # v1: same model, no tools, short prompt
    "v1_gpt51_notools": dict(model="gpt-5.1", prompt=SHORT_PROMPT, tools="", kwargs=NO_REASON, steps=1),
    # v2: same, but 1 output token max
    "v2_gpt51_1tok": dict(model="gpt-5.1", prompt=SHORT_PROMPT, tools="",
                          kwargs={"reasoning_effort": "none", "max_completion_tokens": 1}, steps=1),
    # v3: non-reasoning gpt-4.1, no system prompt, logit_bias forces A-D, 1 token
    "v3_gpt41_bias": dict(model="gpt-4.1", prompt="", tools="",
                          kwargs={"max_completion_tokens": 1, "temperature": 0,
                                  "logit_bias": {"32": 100, "33": 100, "34": 100, "35": 100}}, steps=1),
    "v3b_gpt41mini_bias": dict(model="gpt-4.1-mini", prompt="", tools="",
                               kwargs={"max_completion_tokens": 1, "temperature": 0,
                                       "logit_bias": {"32": 100, "33": 100, "34": 100, "35": 100}}, steps=1),
    # v4: gpt-5.1 no prompt at all, 1 token
    "v4_gpt51_noprompt": dict(model="gpt-5.1", prompt="", tools="",
                              kwargs={"reasoning_effort": "none", "max_completion_tokens": 1}, steps=1),
    # v3c: like v3 but with the short prompt, so the first token is meant to be the answer
    "v3c_gpt41_bias_prompt": dict(model="gpt-4.1", prompt=SHORT_PROMPT, tools="",
                                  kwargs={"max_completion_tokens": 1, "temperature": 0,
                                          "logit_bias": {"32": 100, "33": 100, "34": 100, "35": 100}}, steps=1),
    # v6: newer models, no tools, short prompt, 1 token
    "v6_gpt54_1tok": dict(model="gpt-5.4", prompt=SHORT_PROMPT, tools="",
                          kwargs={"reasoning_effort": "none", "max_completion_tokens": 1}, steps=1),
    "v6b_gpt54mini_1tok": dict(model="gpt-5.4-mini", prompt=SHORT_PROMPT, tools="",
                               kwargs={"reasoning_effort": "none", "max_completion_tokens": 1}, steps=1),
    # v7: brief hidden reasoning instead of tools: tokens only spent where the question needs them
    "v7_gpt51_low": dict(model="gpt-5.1", prompt=SHORT_PROMPT, tools="",
                         kwargs={"reasoning_effort": "low", "max_completion_tokens": 2000}, steps=1),
    "v7b_gpt54_low": dict(model="gpt-5.4", prompt=SHORT_PROMPT, tools="",
                          kwargs={"reasoning_effort": "low", "max_completion_tokens": 2000}, steps=1),
    "v7c_gpt54mini_low": dict(model="gpt-5.4-mini", prompt=SHORT_PROMPT, tools="",
                              kwargs={"reasoning_effort": "low", "max_completion_tokens": 2000}, steps=1),
    "v7d_gpt54_none": dict(model="gpt-5.4", prompt=SHORT_PROMPT, tools="",
                           kwargs={"reasoning_effort": "none", "max_completion_tokens": 16}, steps=1),
    # v8: calculator only, both tools' worth of letter questions handled by the model
    "v8_gpt54_calc": dict(model="gpt-5.4", prompt="Use calculate for math. Reply with only the option letter.",
                          tools="calculate", kwargs={"reasoning_effort": "none", "max_completion_tokens": 50}, steps=2),
    "v9_gpt54_low_tiny": dict(model="gpt-5.4", prompt="Letter only.", tools="",
                              kwargs={"reasoning_effort": "low", "max_completion_tokens": 2000}, steps=1),
    "v9b_gpt54mini_low_tiny": dict(model="gpt-5.4-mini", prompt="Letter only.", tools="",
                                   kwargs={"reasoning_effort": "low", "max_completion_tokens": 2000}, steps=1),
    # p1: the shipped agent.py pipeline (QuickAnswer -> Agent gpt-5.4 low -> BranchJoiner)
    "p1_pipeline": dict(target="agent.py"),
    # luna: the gpt-5.6-luna fork from the platform, same pipeline as agent.py
    "luna_fork": dict(target="evals/pipeline_variant.py", model="gpt-5.6-luna", prompt="", kwargs={}),
    "luna_tuned": dict(target="evals/pipeline_variant.py", model="gpt-5.6-luna", prompt=SHORT_PROMPT,
                       kwargs={"reasoning_effort": "low", "max_completion_tokens": 1000}),
    # p8_*: eight models in the deployed pipeline, each with its best settings
    **{f"p8_{m}": dict(target="evals/pipeline_variant.py", model=m, prompt=SHORT_PROMPT,
                       kwargs={"reasoning_effort": "low", "max_completion_tokens": 1000})
       for m in ("gpt-5.6-luna", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.1", "gpt-5-mini")},
    **{f"p8_{m}": dict(target="evals/pipeline_variant.py", model=m, prompt=SHORT_PROMPT,
                       kwargs={"max_completion_tokens": 1, "temperature": 0,
                               "logit_bias": {"32": 100, "33": 100, "34": 100, "35": 100}})
       for m in ("gpt-4.1", "gpt-4o-mini")},
    # v5: gpt-5.1, only count_letter tool (letter counting is where LLMs slip)
    "v5_gpt51_lettertool": dict(model="gpt-5.1", prompt=SHORT_PROMPT, tools="count_letter",
                                kwargs=NO_REASON, steps=2),
}


def run_one(variant: dict, q):
    question, options, answer = q[:3]
    extra = dict(category=q[3], difficulty=q[4]) if len(q) > 4 else {}
    env = dict(os.environ, QZ_MODEL=variant.get("model", ""), QZ_PROMPT=variant.get("prompt", ""),
               QZ_TOOLS=variant.get("tools", ""), QZ_KWARGS=json.dumps(variant.get("kwargs", {})),
               QZ_STEPS=str(variant.get("steps", 3)))
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "r.json"
        start = time.monotonic()
        run = subprocess.run(
            ["haystack-enterprise", "run", str(ROOT / variant["target"]) if "target" in variant else str(HERE / "agent_variant.py"), "--io-config", str(ROOT / variant.get("io", "agent.io.yaml" if "target" in variant else "evals/agent_variant.io.yaml")),
             "--python", str(ROOT / ".venv/bin/python"), "--query", format_question(question, options),
             "--output", str(out)],
            capture_output=True, text=True, env=env, cwd=ROOT,
        )
        secs = time.monotonic() - start
        if run.returncode != 0 or not out.exists():
            return dict(q=question, answer=answer, reply=None, ok=False, tokens=0, secs=secs, **extra,
                        error=(run.stdout + run.stderr)[-600:])
        result = json.loads(out.read_text())
    reply = last_reply(result).strip()
    return dict(q=question, answer=answer, reply=reply, **extra, ok=bool(re.fullmatch(r"[ABCD]", reply)) and reply == answer,
                tokens=tokens_used(result), secs=secs)


def main(names):
    (HERE / "results").mkdir(exist_ok=True)
    for name in names:
        variant = VARIANTS[name]
        with ThreadPoolExecutor(max_workers=int(os.environ.get("QZ_WORKERS", "10"))) as pool:
            rows = list(pool.map(lambda q: run_one(variant, q), QUESTIONS))
        (HERE / "results" / f"{name}{os.environ.get('QZ_TAG', '')}.json").write_text(json.dumps(rows, indent=1))
        correct = sum(r["ok"] for r in rows)
        tokens = sum(r["tokens"] for r in rows)
        secs = sorted(r["secs"] for r in rows)
        print(f"\n### {name}: {correct}/{len(rows)} correct | {tokens} tokens "
              f"({tokens / len(rows):.0f}/q) | median {secs[len(secs) // 2]:.1f}s, max {secs[-1]:.1f}s")
        for r in rows:
            if not r["ok"]:
                print(f"   ✗ {r['q'][:70]!r} expected {r['answer']} got {r['reply']!r} {r.get('error', '')[:300]}")


if __name__ == "__main__":
    main(sys.argv[1:] or list(VARIANTS))
