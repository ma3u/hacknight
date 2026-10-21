"""Build the static GitHub Pages version of the Vinland pub quiz: python frontend/build_static.py [site]

GitHub Pages has no backend, and the agents' credentials must never ship to a public page. So the
online quiz is a replay: the human plays live, the eight AI models answer with their real recorded
eval answers and tokens, timed with each model's measured isolated median.

- With evals/results/ present (local), regenerates frontend/replay.json from the eval runs.
- Always builds <site>/ (default: site) from index.html, sounds/ and replay.json.
"""

import json
import shutil
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESULTS = HERE.parent / "evals" / "results"
REPLAY = HERE / "replay.json"
MODELS = {
    "gpt-5.4-mini": "Service quiz · reasoning low",
    "gpt-5.6-luna": "Service quiz-luna · reasoning low",
    "gpt-5.4": "reasoning low",
    "gpt-5.4-nano": "reasoning low",
    "gpt-5.1": "reasoning low",
    "gpt-5-mini": "reasoning low",
    "gpt-4.1": "1 Token, logit_bias A-D",
    "gpt-4o-mini": "1 Token, logit_bias A-D",
}
RUNS = ("own", "hard", "s200")  # question sets every model answered


def build_replay() -> None:
    agents, questions = {}, {}
    for model, note in MODELS.items():
        speed = json.loads((RESULTS / f"p8_{model}_speed.json").read_text())
        median = round(statistics.median(r["secs"] for r in speed if r["reply"] is not None), 1)
        agents[model] = {"label": model, "model": model, "note": f"{note} · Replay", "speed": median}
        for run in RUNS:
            for r in json.loads((RESULTS / f"p8_{model}_{run}.json").read_text()):
                q = questions.setdefault(r["q"], {"question": r["q"], "answer": r["answer"], "answers": {}, "run": run})
                if q["run"] != run:  # same text in two sets with different option order: ambiguous, skip it
                    q["conflict"] = True
                    continue
                reply = (r["reply"] or "").strip()
                q["answers"][model] = [reply if reply in ("A", "B", "C", "D") else None, reply[:40], r["tokens"], median]
    # options are not in the result rows: take them from the question sets
    sets = HERE.parent / "evals"
    options = {}
    for name in ("questions.json", "questions_hard.json", "trivia/questions_trivia.json"):
        for row in json.loads((sets / name).read_text()):
            options.setdefault(row[0], row[1])  # own sets first: they own the shared texts
    complete = [{k2: v for k2, v in dict(q, options=options[k]).items() if k2 != "run"} for k, q in questions.items()
                if len(q["answers"]) == len(MODELS) and k in options and not q.get("conflict")]
    REPLAY.write_text(json.dumps({"agents": agents, "questions": complete}, ensure_ascii=False, separators=(",", ":")))
    print(f"replay.json: {len(complete)} questions x {len(agents)} models")


def build_site(out: Path) -> None:
    shutil.rmtree(out, ignore_errors=True)
    (out / "sounds").mkdir(parents=True)
    html = (HERE / "index.html").read_text().replace('<html lang="de">', '<html lang="de" data-static="1">', 1)
    (out / "index.html").write_text(html)
    shutil.copy(REPLAY, out / "replay.json")
    sounds = sorted(p.stem for p in (HERE / "sounds").glob("*.mp3"))
    for name in sounds:
        shutil.copy(HERE / "sounds" / f"{name}.mp3", out / "sounds")
    (out / "sounds.json").write_text(json.dumps({"files": sounds}))
    (out / ".nojekyll").write_text("")
    print(f"site: {out} ({len(sounds)} sounds)")


if __name__ == "__main__":
    if RESULTS.exists():
        build_replay()
    build_site(Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parent / "site")
