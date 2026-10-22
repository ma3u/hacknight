# Team Vinland · Verbesserungen im Überblick

Vom Starter-Agent der deepset Hack Night (21. Oktober 2026, NVIDIA GTC Berlin, „House of Sovereignty“) bis zum
Agent mit Websuche. Jede Stufe wurde mit [`evals/run_eval.py`](../evals/run_eval.py) gemessen und nur übernommen,
wenn die Genauigkeit nicht sank. Details und Diagramme: [`STRATEGY.md`](STRATEGY.md), Tabelle aller Agents:
[`evals/RESULTS.md`](../evals/RESULTS.md).

## Der Weg des Agents

| Stufe | Was sich geändert hat | Genauigkeit | Tokens/Frage | Commit |
|---|---|---|---|---|
| 0 · Starter | gpt-5.1 mit Tools `calculate` und `count_letter`, langer Prompt | 39/40 | 460 | [`856ec43`](https://github.com/ma3u/hacknight/commit/856ec43) |
| 1 · Weniger senden | gpt-5.4, keine Tools, `reasoning_effort: low`, Prompt mit 7 Wörtern | 60/60 | 66–82 | [`aaa8ee8`](https://github.com/ma3u/hacknight/commit/aaa8ee8) |
| 2 · Python statt LLM | `QuickAnswer`-Komponente löst Rechen- und Zählfragen mit 0 Tokens; Pipeline mit `BranchJoiner` | 60/60 | 46–52 | [`b01d514`](https://github.com/ma3u/hacknight/commit/b01d514) |
| 3 · Bestes Modell | 8 Modelle gemessen; gpt-5.4-mini ist am genauesten und unter den genauen am schnellsten | 200/200 Trivia, 59/60 eigene | 69 | [`b01d514`](https://github.com/ma3u/hacknight/commit/b01d514) |
| 4 · Websuche | `ConditionalRouter` schickt aktuelle Fragen an einen Agent mit OpenAI-Websuche | **14/14 aktuell** (vorher 4/14), 174/174 gesamt | ~75 zeitlos, ~9.000 mit Suche | [`457c944`](https://github.com/ma3u/hacknight/commit/457c944) |

**Ergebnis:** 99,6 % über alle Testsets, ~3,6 s bei normalen Fragen und ~7 s mit Websuche, gegenüber dem
Starter-Agent etwa 90 % weniger Tokens pro normaler Frage.

## Was wir gelernt haben

1. **Tokens zählen, nicht Modellpreise.** Das Leaderboard wertete Tokens modellunabhängig. Tool-Beschreibungen und
   lange Prompts werden bei jeder Frage bezahlt; jeder Tool-Aufruf ist ein zweiter LLM-Aufruf.
2. **Denken nur, wo es nötig ist.** `reasoning_effort: low` kostet bei Wissensfragen genauso viele Tokens wie `none`,
   rechnet Textaufgaben aber richtig.
3. **Was Python kann, braucht kein LLM.** Der Solver antwortet nur, wenn genau eine Option passt; sonst übernimmt das
   Modell.
4. **Faire Messung braucht gleiche Bedingungen.** Acht Agents parallel in der Sandbox maßen vor allem die
   Warteschlange (6–14 s statt 2–4 s); ein Lauf nach dem anderen trennt die Modelle.
5. **Das Format ist Teil der Genauigkeit.** Der Luna-Fork verlor ohne Systemprompt 999 von 1.000 Fragen
   („D) Inception“ statt „D“), obwohl er 962 wusste. Astra antwortete mit niedrigem Reasoning „I don't know.“ —
   „If unsure, guess.“ im Prompt behebt beides.
6. **Wissen, das nicht im Modell steckt, muss gesucht werden.** Die Gewinner nutzten das größte Modell (Astra) und
   Websuche. Gemessen: Astra kennt 7 von 14 aktuellen Ereignissen, mit Websuche schaffen beide Modelle 14/14.
7. **Suche nur, wenn sie nötig ist.** Suchergebnisse kosten ~9.000 Tokens. Ein Router entscheidet vorab anhand der
   Fragezeile (2025/2026, latest, current, kleingeschriebenes „new“), sodass normale Fragen schlank bleiben.
8. **Erst nachsehen, dann glauben.** Die erste Messung „mit Websuche“ sah nach wenig Nutzen aus; tatsächlich lieferte
   die Serper-Suche HTTP 403, weil `SERPERDEV_API_KEY` nur als Org-Secret existiert. Erst der Blick in die
   Nachrichten des Agents zeigte das. OpenAIs gehostete Websuche läuft mit dem vorhandenen OpenAI-Key.

## Plattform-Erkenntnisse (Haystack Enterprise)

- **Secrets:** Die Sandbox (`haystack-enterprise run`) und Deploys sehen Integrationen (OpenAI) und Workspace-Secrets,
  aber keine reinen Org-Secrets. Ein Deploy mit fehlendem Secret wird bei der Validierung abgelehnt.
- **Code-Komponenten:** Eigene `@component`-Klassen werden als Code-Komponente deployt; Init-Parameter kommen
  serialisiert an (ein `Secret` als Dictionary).
- **Zwei Agents in einer Pipeline:** Die Plattform streamt nur einen. Die Chat-Completions-Option `stream_options`
  scheitert dann beim anderen; die Responses API meldet Tokens in beiden Fällen.
- **Tools und Reasoning:** OpenAI erlaubt Funktions-Tools zusammen mit `reasoning_effort` nur über die Responses API.
- **Kaltstart:** Serverless-Services gehen in Standby; die erste Frage nach einer Pause brauchte 10–18 s (Limit 15 s).
  Vor dem Quiz aufwärmen.

## Rund um den Agent

| Baustein | Inhalt |
|---|---|
| Evals | 60 eigene Fragen, 1.000 Fragen aus The Trivia API ([Tabelle](../evals/trivia/QUESTIONS.md)), 14 belegte Fragen zu aktuellen Ereignissen |
| Luna-Fix | [`agent_luna.py`](../agent_luna.py): gleiche Pipeline mit gpt-5.6-luna, Service `quiz-luna`; von 1/1000 auf 993/1000 |
| Frontend | Vinland Pub Quiz: ein Mensch gegen 10 KI-Agenten, historische Wikinger-Figuren, Rekordleiste, ElevenLabs-Sound |
| Online | [ma3u.github.io/hacknight](https://ma3u.github.io/hacknight/): Replay mit den echten Eval-Antworten, per GitHub Actions deployt |
| Video | [`video/record_video.py`](../video/record_video.py): Chrome-Aufnahme per DevTools-Screencast, Opus 5.5 spielt den Menschen, LinkedIn (4:5) und Desktop (16:9) |
| LinkedIn | Der veröffentlichte Post: [`LINKEDIN.md`](LINKEDIN.md) |
