# Team Vinland · Improvements at a glance

From the starter agent of the deepset Hack Night (October 21, 2026, NVIDIA GTC Berlin, "House of Sovereignty") to the
agent with web search. Every stage was measured with [`evals/run_eval.py`](../evals/run_eval.py) and only kept if
accuracy didn't drop. Details and diagrams: [`STRATEGY.md`](STRATEGY.md); all agents compared:
[`evals/RESULTS.md`](../evals/RESULTS.md).

## The agent's path

| Stage | What changed | Accuracy | Tokens/question | Commit |
|---|---|---|---|---|
| 0 · Starter | gpt-5.1 with the tools `calculate` and `count_letter`, long prompt | 39/40 | 460 | [`856ec43`](https://github.com/ma3u/hacknight/commit/856ec43) |
| 1 · Send less | gpt-5.4, no tools, `reasoning_effort: low`, seven-word prompt | 60/60 | 66–82 | [`aaa8ee8`](https://github.com/ma3u/hacknight/commit/aaa8ee8) |
| 2 · Python instead of an LLM | `QuickAnswer` component solves arithmetic and letter counts with 0 tokens; pipeline with `BranchJoiner` | 60/60 | 46–52 | [`b01d514`](https://github.com/ma3u/hacknight/commit/b01d514) |
| 3 · Best model | 8 models measured; gpt-5.4-mini is the most accurate and the fastest of the accurate ones | 200/200 trivia, 59/60 own | 69 | [`b01d514`](https://github.com/ma3u/hacknight/commit/b01d514) |
| 4 · Web search | `ConditionalRouter` sends recent questions to an agent with OpenAI web search | **14/14 recent** (was 4/14), 174/174 overall | ~75 timeless, ~9,000 with search | [`457c944`](https://github.com/ma3u/hacknight/commit/457c944) |

**Result:** 99.6 % across all test sets, ~3.6 s for normal questions and ~7 s with web search, and about 90 % fewer
tokens per normal question than the starter agent.

## What we learned

1. **Count tokens, not model prices.** The leaderboard counted tokens regardless of model. Tool descriptions and long
   prompts are paid on every question; every tool call is a second LLM call.
2. **Think only where it's needed.** `reasoning_effort: low` costs exactly as many tokens as `none` on knowledge
   questions, but gets word problems right.
3. **What Python can do needs no LLM.** The solver only answers when exactly one option matches; otherwise the model
   takes over.
4. **Fair measurement needs equal conditions.** Eight agents in parallel in the sandbox mostly measured the queue
   (6–14 s instead of 2–4 s); one run at a time separates the models.
5. **Format is part of accuracy.** Without a system prompt the Luna fork lost 999 of 1,000 questions
   ("D) Inception" instead of "D") although it knew 962 of them. Astra answered "I don't know." on low reasoning —
   "If unsure, guess." in the prompt fixes both.
6. **Knowledge that isn't in the model has to be searched.** The winners used the biggest model (Astra) and web search.
   Measured: Astra knows 7 of 14 recent events; with web search both models get 14/14.
7. **Search only when it's needed.** Search results cost ~9,000 tokens. A router decides up front from the question line
   (2025/2026, latest, current, lowercase "new"), so normal questions stay lean.
8. **Look before you believe.** The first measurement "with web search" suggested little benefit; in fact the Serper
   search returned HTTP 403 because `SERPERDEV_API_KEY` exists only as an org secret. Only the agent's messages showed
   that. OpenAI's hosted web search runs on the existing OpenAI key.

## Platform findings (Haystack Enterprise)

- **Secrets:** the sandbox (`haystack-enterprise run`) and deploys see integrations (OpenAI) and workspace secrets, but
  not plain org secrets. A deploy with a missing secret is rejected during validation.
- **Code components:** custom `@component` classes are deployed as code components; init parameters arrive serialized
  (a `Secret` as a dictionary).
- **Two agents in one pipeline:** the platform streams only one of them. The Chat Completions option `stream_options`
  then fails for the other; the Responses API reports tokens either way.
- **Tools and reasoning:** OpenAI only allows function tools together with `reasoning_effort` on the Responses API.
- **Cold start:** serverless services go to standby; the first question after a pause took 10–18 s (limit 15 s).
  Warm up before the quiz.

## Around the agent

| Building block | Contents |
|---|---|
| Evals | 60 own questions, 1,000 questions from The Trivia API ([table](../evals/trivia/QUESTIONS.md)), 14 sourced recent-events questions |
| Luna fix | [`agent_luna.py`](../agent_luna.py): same pipeline with gpt-5.6-luna, service `quiz-luna`; from 1/1000 to 993/1000 |
| Frontend | Vinland Pub Quiz: one human vs. ten AI agents, historical Viking characters, records bar, ElevenLabs sound |
| Online | [ma3u.github.io/hacknight](https://ma3u.github.io/hacknight/): replay with the real eval answers, deployed by GitHub Actions |
| Video | [`video/record_video.py`](../video/record_video.py): Chrome recording via the DevTools screencast, Opus 5.5 plays the human, LinkedIn (4:5) and desktop (16:9) |
| LinkedIn | The published post: [`LINKEDIN.md`](LINKEDIN.md) |
