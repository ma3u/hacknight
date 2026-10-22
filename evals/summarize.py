"""Accuracy and speed per agent, from the result files in evals/results/: uv run python evals/summarize.py

Writes evals/RESULTS.md. Ranked like the goal: most accurate first, then fastest.
Speed is the isolated median (one run at a time, same 10 questions), so it compares models, not queues.
"""

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
# agent -> eval result prefix
PREFIX = {"gpt-5.4-mini + web search": "p2_web", "gpt-6-astra": "w_astra",
          **{m: f"p8_{m}" for m in ("gpt-5.4-mini", "gpt-5.6-luna", "gpt-5.4", "gpt-5.4-nano", "gpt-5.1", "gpt-5-mini",
                                    "gpt-4.1", "gpt-4o-mini")}}
MODELS = list(PREFIX)
FULL_1000 = {"gpt-5.4-mini": "p8_gpt-5.4-mini_trivia", "gpt-5.4": "p1_pipeline_trivia", "gpt-5.6-luna": "luna_tuned_trivia"}
SERVICES = {"gpt-5.4-mini + web search": "quiz"}
CHARACTERS = {"gpt-5.4-mini + web search": "Snorri Thorfinnsson", "gpt-6-astra": "Thorvald Eriksson",
              "gpt-5.4-mini": "Thorfinn Karlsefni", "gpt-5.6-luna": "Thorkell the Tall", "gpt-5.4": "Freydís Eiríksdóttir",
              "gpt-5.4-nano": "Guðríður Þorbjarnardóttir", "gpt-5.1": "Erik the Red", "gpt-5-mini": "Bjarni Herjólfsson", "gpt-4.1": "Harald Bluetooth",
              "gpt-4o-mini": "Olaf Tryggvason"}


def load(name):
    path = RESULTS / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def score(rows):
    return f"{sum(r['ok'] for r in rows)}/{len(rows)}" if rows else "–"


def main():
    table = []
    for m in MODELS:
        p = PREFIX[m]
        own = (load(f"{p}_own") or []) + (load(f"{p}_hard") or [])
        sample, full, speed = load(f"{p}_s200"), load(FULL_1000[m]) if m in FULL_1000 else None, load(f"{p}_speed")
        recent = load(f"{p}_recent")
        everything = [r for rows in (own, sample, speed, recent) if rows for r in rows]
        correct = sum(r["ok"] for r in everything) / len(everything) if everything else 0
        median = statistics.median(r["secs"] for r in speed if r["reply"] is not None) if speed else float("nan")
        tokens = sum(r["tokens"] for r in everything) / len(everything) if everything else 0
        table.append((correct, median, m, own, sample, full, speed, tokens, recent))
    table.sort(key=lambda t: (-t[0], t[1]))

    lines = ["# Accuracy and speed per agent", "",
             "All agents: same pipeline (QuickAnswer solver → agent → BranchJoiner), same prompt, each with its best settings",
             "(reasoning models `reasoning_effort: low`; gpt-4.1/gpt-4o-mini 1 token with `logit_bias` A–D).",
             "Sorted by the goal: **accurate first, then fast**.", "",
             "| # | Agent | Character | Service | Overall accuracy | Recent events 14 | Own 60 (incl. arithmetic/word problems) | Trivia 200 | Trivia 1000 | Speed (median, isolated) | Tokens/question |",
             "|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, (correct, median, m, own, sample, full, speed, tokens, recent) in enumerate(table, 1):
        lines.append(f"| {i} | **{m}** | {CHARACTERS[m]} | {SERVICES.get(m, '–')} | {correct:.1%} | {score(recent)} | {score(own)} | "
                     f"{score(sample)} | {score(full)} | {median:.1f} s | {tokens:,.0f} |")
    lines += ["", "- *Overall accuracy* = recent 14 + own 60 + trivia 200 + speed sample 10 (without trivia 1000, which not every model ran).",
              "- *Recent events* = questions about July–October 2026 (World Cup, Nobel Prizes, Tour, Wimbledon, GTC Berlin, GPT-6 Astra).",
              "  Only the agent with web search answers them reliably; it searches only when the router detects a recent question.",
              "- *Speed* = median of 10 questions, one run at a time in the platform sandbox (incl. ~1 s of local CLI preparation).",
              "  The deployed `quiz` service answers in ~1.5 s when warm; questions with web search take ~7 s (max 10 s measured).",
              "- *Tokens/question* of the web agent: ~75 on timeless questions, ~9,000 on the 14 search questions (search results).",
              "- Known error in the trivia dataset: dromedary humps keyed as 0 instead of 1."]
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
