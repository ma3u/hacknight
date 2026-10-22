# Accuracy and speed per agent

All agents: same pipeline (QuickAnswer solver → agent → BranchJoiner), same prompt, each with its best settings
(reasoning models `reasoning_effort: low`; gpt-4.1/gpt-4o-mini 1 token with `logit_bias` A–D).
Sorted by the goal: **accurate first, then fast**.

| # | Agent | Character | Service | Overall accuracy | Recent events 14 | Own 60 (incl. arithmetic/word problems) | Trivia 200 | Trivia 1000 | Speed (median, isolated) | Tokens/question |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **gpt-5.4-mini + web search** | Snorri Thorfinnsson | quiz | 99.6% | 14/14 | 60/60 | 199/200 | – | 3.6 s | 553 |
| 2 | **gpt-6-astra** | Thorvald Eriksson | – | 97.2% | 7/14 | 59/60 | 200/200 | – | 3.4 s | 64 |
| 3 | **gpt-5.4** | Freydís Eiríksdóttir | – | 96.5% | 6/14 | 59/60 | 199/200 | 993/1000 | 3.4 s | 78 |
| 4 | **gpt-5.1** | Erik the Red | – | 96.1% | 4/14 | 59/60 | 200/200 | – | 3.6 s | 71 |
| 5 | **gpt-5.4-mini** | Thorfinn Karlsefni | – | 95.8% | 3/14 | 59/60 | 200/200 | 992/1000 | 3.0 s | 78 |
| 6 | **gpt-5-mini** | Bjarni Herjólfsson | – | 95.4% | 3/14 | 59/60 | 199/200 | – | 3.6 s | 85 |
| 7 | **gpt-4.1** | Harald Bluetooth | – | 95.1% | 4/14 | 57/60 | 199/200 | – | 3.0 s | 53 |
| 8 | **gpt-5.6-luna** | Thorkell the Tall | – | 95.1% | 6/14 | 57/60 | 197/200 | 993/1000 | 3.4 s | 65 |
| 9 | **gpt-4o-mini** | Olaf Tryggvason | – | 92.3% | 2/14 | 55/60 | 195/200 | – | 2.8 s | 53 |
| 10 | **gpt-5.4-nano** | Guðríður Þorbjarnardóttir | – | 92.3% | 4/14 | 58/60 | 191/200 | – | 4.7 s | 73 |

- *Overall accuracy* = recent 14 + own 60 + trivia 200 + speed sample 10 (without trivia 1000, which not every model ran).
- *Recent events* = questions about July–October 2026 (World Cup, Nobel Prizes, Tour, Wimbledon, GTC Berlin, GPT-6 Astra).
  Only the agent with web search answers them reliably; it searches only when the router detects a recent question.
- *Speed* = median of 10 questions, one run at a time in the platform sandbox (incl. ~1 s of local CLI preparation).
  The deployed `quiz` service answers in ~1.5 s when warm; questions with web search take ~7 s (max 10 s measured).
- *Tokens/question* of the web agent: ~75 on timeless questions, ~9,000 on the 14 search questions (search results).
- Known error in the trivia dataset: dromedary humps keyed as 0 instead of 1.
