"""Accuracy and speed per agent, from the result files in evals/results/: uv run python evals/summarize.py

Writes evals/RESULTS.md. Ranked like the goal: most accurate first, then fastest.
Speed is the isolated median (one run at a time, same 10 questions), so it compares models, not queues.
"""

import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
MODELS = ["gpt-5.4-mini", "gpt-5.6-luna", "gpt-5.4", "gpt-5.4-nano", "gpt-5.1", "gpt-5-mini", "gpt-4.1", "gpt-4o-mini"]
FULL_1000 = {"gpt-5.4-mini": "p8_gpt-5.4-mini_trivia", "gpt-5.4": "p1_pipeline_trivia", "gpt-5.6-luna": "luna_tuned_trivia"}
SERVICES = {"gpt-5.4-mini": "quiz", "gpt-5.6-luna": "quiz-luna"}
CHARACTERS = {"gpt-5.4-mini": "Thorfinn Karlsefni", "gpt-5.6-luna": "Thorkell der Hohe", "gpt-5.4": "Freydís",
              "gpt-5.4-nano": "Guðríður", "gpt-5.1": "Erik der Rote", "gpt-5-mini": "Bjarni", "gpt-4.1": "Harald Blauzahn",
              "gpt-4o-mini": "Olaf Tryggvason"}


def load(name):
    path = RESULTS / f"{name}.json"
    return json.loads(path.read_text()) if path.exists() else None


def score(rows):
    return f"{sum(r['ok'] for r in rows)}/{len(rows)}" if rows else "–"


def main():
    table = []
    for m in MODELS:
        own = (load(f"p8_{m}_own") or []) + (load(f"p8_{m}_hard") or [])
        sample, full, speed = load(f"p8_{m}_s200"), load(FULL_1000[m]) if m in FULL_1000 else None, load(f"p8_{m}_speed")
        everything = [r for rows in (own, sample, speed) if rows for r in rows]
        correct = sum(r["ok"] for r in everything) / len(everything) if everything else 0
        median = statistics.median(r["secs"] for r in speed if r["reply"] is not None) if speed else float("nan")
        tokens = sum(r["tokens"] for r in everything) / len(everything) if everything else 0
        table.append((correct, median, m, own, sample, full, speed, tokens))
    table.sort(key=lambda t: (-t[0], t[1]))

    lines = ["# Genauigkeit und Geschwindigkeit pro Agent", "",
             "Alle Agents: gleiche Pipeline (QuickAnswer-Solver → Agent → BranchJoiner), gleicher Prompt, jeweils beste Einstellung",
             "(Reasoning-Modelle `reasoning_effort: low`; gpt-4.1/gpt-4o-mini 1 Token mit `logit_bias` A–D).",
             "Sortiert nach dem Ziel: **genau zuerst, dann schnell**.", "",
             "| # | Modell | Figur | Service | Genauigkeit gesamt | Eigene 60 (inkl. Rechen-/Textaufgaben) | Trivia 200 | Trivia 1000 | Speed (Median, isoliert) | Tokens/Frage |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for i, (correct, median, m, own, sample, full, speed, tokens) in enumerate(table, 1):
        lines.append(f"| {i} | **{m}** | {CHARACTERS[m]} | {SERVICES.get(m, '–')} | {correct:.1%} | {score(own)} | {score(sample)} | "
                     f"{score(full)} | {median:.1f} s | {tokens:.0f} |")
    lines += ["", "- *Genauigkeit gesamt* = eigene 60 + Trivia 200 + Speed-Stichprobe 10 (ohne Trivia 1000, die nicht alle Modelle haben).",
              "- *Speed* = Median von 10 Fragen, ein Lauf nach dem anderen in der Plattform-Sandbox (inkl. ~1 s lokaler CLI-Vorbereitung).",
              "  Der deployte Service `quiz` antwortet warm in ~1,5 s.",
              "- Bekannter Fehler im Trivia-Datensatz: Dromedar-Höcker als 0 statt 1 gewertet."]
    (HERE / "RESULTS.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
