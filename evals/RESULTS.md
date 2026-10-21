# Genauigkeit und Geschwindigkeit pro Agent

Alle Agents: gleiche Pipeline (QuickAnswer-Solver → Agent → BranchJoiner), gleicher Prompt, jeweils beste Einstellung
(Reasoning-Modelle `reasoning_effort: low`; gpt-4.1/gpt-4o-mini 1 Token mit `logit_bias` A–D).
Sortiert nach dem Ziel: **genau zuerst, dann schnell**.

| # | Modell | Figur | Service | Genauigkeit gesamt | Eigene 60 (inkl. Rechen-/Textaufgaben) | Trivia 200 | Trivia 1000 | Speed (Median, isoliert) | Tokens/Frage |
|---|---|---|---|---|---|---|---|---|---|
| 1 | **gpt-5.4-mini** | Thorfinn Karlsefni | quiz | 99.6% | 59/60 | 200/200 | 992/1000 | 3.0 s | 69 |
| 2 | **gpt-5.1** | Erik der Rote | – | 99.6% | 59/60 | 200/200 | – | 3.6 s | 66 |
| 3 | **gpt-5.4** | Freydís | – | 99.3% | 59/60 | 199/200 | 993/1000 | 3.4 s | 70 |
| 4 | **gpt-5-mini** | Bjarni | – | 99.3% | 59/60 | 199/200 | – | 3.6 s | 73 |
| 5 | **gpt-4.1** | Harald Blauzahn | – | 98.5% | 57/60 | 199/200 | – | 3.0 s | 53 |
| 6 | **gpt-5.6-luna** | Thorkell der Hohe | quiz-luna | 97.8% | 57/60 | 197/200 | 993/1000 | 3.4 s | 56 |
| 7 | **gpt-4o-mini** | Olaf Tryggvason | – | 96.3% | 55/60 | 195/200 | – | 2.8 s | 53 |
| 8 | **gpt-5.4-nano** | Guðríður | – | 95.6% | 58/60 | 191/200 | – | 4.7 s | 69 |

- *Genauigkeit gesamt* = eigene 60 + Trivia 200 + Speed-Stichprobe 10 (ohne Trivia 1000, die nicht alle Modelle haben).
- *Speed* = Median von 10 Fragen, ein Lauf nach dem anderen in der Plattform-Sandbox (inkl. ~1 s lokaler CLI-Vorbereitung).
  Der deployte Service `quiz` antwortet warm in ~1,5 s.
- Bekannter Fehler im Trivia-Datensatz: Dromedar-Höcker als 0 statt 1 gewertet.
