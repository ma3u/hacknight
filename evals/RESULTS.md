# Genauigkeit und Geschwindigkeit pro Agent

Alle Agents: gleiche Pipeline (QuickAnswer-Solver → Agent → BranchJoiner), gleicher Prompt, jeweils beste Einstellung
(Reasoning-Modelle `reasoning_effort: low`; gpt-4.1/gpt-4o-mini 1 Token mit `logit_bias` A–D).
Sortiert nach dem Ziel: **genau zuerst, dann schnell**.

| # | Agent | Figur | Service | Genauigkeit gesamt | Aktuelle Ereignisse 14 | Eigene 60 (inkl. Rechen-/Textaufgaben) | Trivia 200 | Trivia 1000 | Speed (Median, isoliert) | Tokens/Frage |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | **gpt-5.4-mini + Websuche** | Snorri Thorfinnsson | quiz | 99.6% | 14/14 | 60/60 | 199/200 | – | 3.6 s | 553 |
| 2 | **gpt-6-astra** | Thorvald Eriksson | – | 97.2% | 7/14 | 59/60 | 200/200 | – | 3.4 s | 64 |
| 3 | **gpt-5.4** | Freydís | – | 96.5% | 6/14 | 59/60 | 199/200 | 993/1000 | 3.4 s | 78 |
| 4 | **gpt-5.1** | Erik der Rote | – | 96.1% | 4/14 | 59/60 | 200/200 | – | 3.6 s | 71 |
| 5 | **gpt-5.4-mini** | Thorfinn Karlsefni | – | 95.8% | 3/14 | 59/60 | 200/200 | 992/1000 | 3.0 s | 78 |
| 6 | **gpt-5-mini** | Bjarni | – | 95.4% | 3/14 | 59/60 | 199/200 | – | 3.6 s | 85 |
| 7 | **gpt-4.1** | Harald Blauzahn | – | 95.1% | 4/14 | 57/60 | 199/200 | – | 3.0 s | 53 |
| 8 | **gpt-5.6-luna** | Thorkell der Hohe | – | 95.1% | 6/14 | 57/60 | 197/200 | 993/1000 | 3.4 s | 65 |
| 9 | **gpt-4o-mini** | Olaf Tryggvason | – | 92.3% | 2/14 | 55/60 | 195/200 | – | 2.8 s | 53 |
| 10 | **gpt-5.4-nano** | Guðríður | – | 92.3% | 4/14 | 58/60 | 191/200 | – | 4.7 s | 73 |

- *Genauigkeit gesamt* = aktuelle 14 + eigene 60 + Trivia 200 + Speed-Stichprobe 10 (ohne Trivia 1000, die nicht alle Modelle haben).
- *Aktuelle Ereignisse* = Fragen zu Juli–Oktober 2026 (WM, Nobelpreise, Tour, Wimbledon, GTC Berlin, GPT-6 Astra).
  Nur der Agent mit Websuche löst sie zuverlässig; er sucht nur, wenn der Router eine aktuelle Frage erkennt.
- *Speed* = Median von 10 Fragen, ein Lauf nach dem anderen in der Plattform-Sandbox (inkl. ~1 s lokaler CLI-Vorbereitung).
  Der deployte Service `quiz` antwortet warm in ~1,5 s; Fragen mit Websuche brauchen ~7 s (max. 10 s gemessen).
- *Tokens/Frage* des Web-Agents: ~75 bei zeitlosen Fragen, ~9.000 bei den 14 Suchfragen (Suchergebnisse).
- Bekannter Fehler im Trivia-Datensatz: Dromedar-Höcker als 0 statt 1 gewertet.
