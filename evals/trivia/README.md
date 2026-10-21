# 1000 pub quiz questions

Downloaded from [The Trivia API](https://the-trivia-api.com) (questions licensed CC BY-NC 4.0; attribution: The Trivia API)
with [`../fetch_trivia.py`](../fetch_trivia.py).

- `raw.json`: the API responses as downloaded
- [`QUESTIONS.md`](QUESTIONS.md): all 1000 questions as a readable table
- `questions_trivia.json`: `[question, [A, B, C, D], answer letter, category, difficulty]`, options shuffled with seed 42

Run an eval on them:

```bash
QZ_SET=trivia/questions_trivia.json QZ_TAG=_trivia uv run python evals/run_eval.py p1_pipeline
```

Known answer-key errors: "How Many Humps Has A Dromedary Camel Got?" is keyed as 0 (a dromedary has one hump).
