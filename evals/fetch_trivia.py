"""Download multiple-choice pub quiz questions from The Trivia API (https://the-trivia-api.com).

uv run python evals/fetch_trivia.py [N]   -> evals/trivia/questions_trivia.json

Writes the same [question, [A, B, C, D], letter, category, difficulty] shape the eval runner
reads. Options are shuffled with a fixed seed, so the file is reproducible from evals/trivia/raw.json.
(opentdb.com was the first choice but answers 403 from this network.)
"""

import json
import random
import sys
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "trivia"
API = "https://the-trivia-api.com/v2/questions?limit=50"


def get(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": "hacknight-quiz-eval/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read())


def main(target: int) -> None:
    OUT.mkdir(exist_ok=True)
    raw, seen, stale = [], set(), 0
    while len(raw) < target and stale < 10:
        before = len(raw)
        for item in get(API):
            text = item["question"]["text"]
            if item["id"] not in seen and text not in seen and len(item["incorrectAnswers"]) == 3:
                seen.update((item["id"], text))
                raw.append(item)
        stale = stale + 1 if len(raw) == before else 0
        print(f"{len(raw)} questions", flush=True)
        time.sleep(1)
    raw = raw[:target]
    (OUT / "raw.json").write_text(json.dumps(raw, indent=1, ensure_ascii=False))

    rng = random.Random(42)
    questions = []
    for item in raw:
        options = [item["correctAnswer"], *item["incorrectAnswers"]]
        rng.shuffle(options)
        questions.append([item["question"]["text"], options, "ABCD"[options.index(item["correctAnswer"])],
                          item["category"], item["difficulty"]])
    (OUT / "questions_trivia.json").write_text(json.dumps(questions, indent=1, ensure_ascii=False))
    print(f"wrote {len(questions)} questions to {OUT / 'questions_trivia.json'}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)
