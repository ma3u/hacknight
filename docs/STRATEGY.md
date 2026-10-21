# Team Vinland · Strategie für die Quiz Agent Challenge

> hacknight · Haystack Enterprise Platform · Workspace `vinland` · Fork [`ma3u/hacknight`](https://github.com/ma3u/hacknight)

## 1. Aufgabe und Wertung

Der Agent bekommt eine Multiple-Choice-Frage (A–D) und muss mit **genau einem Buchstaben** antworten.
Das Leaderboard wertet in dieser Reihenfolge:

| Rang | Kriterium | Folgerung für uns |
|---|---|---|
| 1 | meiste richtige Antworten (15 s Limit) | Genauigkeit und Format gehen vor allem anderen |
| 2 | wenigste **Tokens** | Tokens zählen modellunabhängig: ein „billiges“ Modell spart Geld, aber keine Tokens |
| 3 | schnellste Gesamtzeit | erst relevant, wenn 1 und 2 gleich sind |

## 2. Strategie in fünf Sätzen

1. **Was nicht gesendet wird, kostet nichts:** Tool-Schemas und lange Systemprompts werden bei *jeder* Frage bezahlt. Darum: keine Tools, ein Prompt aus sieben Wörtern.
2. **Denken nur, wo es nötig ist:** `reasoning_effort: low` kostet bei Wissensfragen exakt so viele Tokens wie `none` (gemessen: Differenz 0), denkt aber bei Rechen- und Textaufgaben kurz nach.
3. **Was Python ausrechnen kann, braucht kein LLM:** Die Komponente `QuickAnswer` löst Buchstaben-Zählfragen und reine Arithmetik exakt, mit **0 Tokens**, und antwortet nur, wenn genau eine Option passt.
4. **Haystack-Bordmittel statt Eigenbau:** `Pipeline`, `Agent`, `OpenAIChatGenerator`, `BranchJoiner` und ein einziger `@component`.
5. **Jede Änderung muss den Eval bestehen:** 60 eigene Fragen plus 1000 Fragen aus [The Trivia API](https://the-trivia-api.com). Eine Änderung bleibt nur, wenn die Genauigkeit nicht sinkt.

## 3. Systemarchitektur

Die PlantUML-Quellen liegen zusätzlich in [`diagrams/`](diagrams/) (neu rendern: `plantuml -tsvg docs/diagrams/*.puml`).

```plantuml
@startuml architecture
!theme plain
skinparam componentStyle rectangle
skinparam shadowing false
title Team Vinland · Systemarchitektur

actor "Quiz-Host\n(Agent Quiz, localhost:3000)" as Host
actor "Team Vinland\n(Browser)" as Team

package "Laptop · Repo ma3u/hacknight" {
  [agent.py\nbuild_pipeline(model)] as AgentPy
  [agent_luna.py] as LunaPy
  [quick_answer.py\n@component QuickAnswer] as QA
  [evals/run_eval.py\n+ questions*.json] as Evals
  [frontend/server.py\n(Proxy, stdlib)] as Server
  [frontend/index.html\nDuell-UI + Sounds] as UI
  [frontend/make_sounds.py\n+ eleven.py] as Sounds
  [haystack-enterprise CLI] as CLI
}

cloud "Haystack Enterprise Platform" {
  node "Gateway" {
    [Service quiz\ngpt-5.4-mini] as SvcQuiz
    [Service quiz-luna\ngpt-5.6-luna] as SvcLuna
  }
  node "Pipeline (beide Services)" {
    [QuickAnswer\n(Code-Komponente)] as PQA
    [Agent\nOpenAIChatGenerator] as PAgent
    [BranchJoiner] as PJoin
  }
  [Sandbox\n(run ohne Deploy)] as Sandbox
  database "Org-Secrets\nOPENAI_API_KEY" as Secrets
}

cloud "OpenAI API" as OpenAI
cloud "ElevenLabs API" as Eleven

AgentPy ..> QA : importiert
LunaPy ..> AgentPy : build_pipeline("gpt-5.6-luna")
CLI --> SvcQuiz : deploy agent.py quiz (gpt-5.4-mini)
CLI --> SvcLuna : deploy agent_luna.py quiz-luna
CLI --> Sandbox : run (check.py, evals, Frontend)
Evals --> CLI
Server --> CLI : Sandbox-Modus
Server --> SvcQuiz : Live-Modus (DEEPSET_API_KEY)
UI --> Server : /api/questions, /api/ask
Team --> UI
Sounds --> Eleven : Sound-Effekte, Musik, Stimmen
Server --> Eleven : Knut liest Fragen vor (TTS)
UI ..> Sounds : sounds/*.mp3

Host --> SvcQuiz : Frage (OpenAI-kompatibel)
SvcQuiz --> PQA
SvcLuna --> PQA
PQA --> PJoin : beantwortet (0 Tokens)
PQA --> PAgent : unbeantwortet
PAgent --> PJoin
PAgent --> OpenAI : 1 Aufruf, reasoning low
Secrets ..> PAgent : OPENAI_API_KEY
@enduml
```

![architecture](diagrams/architecture.svg)

## 4. Sequenzdiagramme

### 4.1 Eine Quizfrage im Live-Quiz

```plantuml
@startuml live-question
!theme plain
skinparam shadowing false
title Live-Quiz · eine Frage an den Service "quiz"

participant "Quiz-Host" as Host
participant "Gateway\nService quiz" as GW
participant "QuickAnswer" as QA
participant "Agent\n(gpt-5.4-mini)" as Agent
participant "OpenAI" as OAI
participant "BranchJoiner" as Join

Host -> GW : POST /chat/completions\n"Frage\nA) …\nB) …\nC) …\nD) …"
GW -> QA : messages
alt berechenbar (Buchstaben zählen, Arithmetik)\nund genau eine Option passt
  QA -> QA : solve() in Python
  QA -> Join : answered = [..., "B"]
  note right of QA : 0 Tokens, Millisekunden
else alles andere
  QA -> Agent : unanswered = messages
  Agent -> OAI : system "Reply with only the correct option letter."\nreasoning_effort=low, include_usage
  OAI --> Agent : "B" (~45 Tokens Wissen, bis ~150 Textaufgabe)
  Agent -> Join : messages + "B"
end
Join --> GW : value
GW --> Host : "B" + usage
note over Host : Wertung: richtig → Tokens → Zeit\n(15 s Limit, Kaltstart vorher aufwärmen!)
@enduml
```

![live-question](diagrams/live-question.svg)

### 4.2 Eval-Iteration (wie jede Änderung geprüft wurde)

```plantuml
@startuml eval-loop
!theme plain
skinparam shadowing false
title Eval-Schleife · Änderung → Messung → Entscheidung

actor Entwickler as Dev
participant "run_eval.py" as Eval
participant "haystack-enterprise run" as CLI
participant "Platform-Sandbox" as SB
participant "OpenAI" as OAI

Dev -> Eval : Variante (Modell, Prompt, Tools, kwargs)
loop jede Frage (10–12 parallel)
  Eval -> CLI : run <pipeline.py> --query "Frage + A–D"
  CLI -> CLI : Pipeline lokal laden, serialisieren,\n@component → Code-Komponente
  CLI -> SB : YAML + Inputs ausführen
  SB -> OAI : Chat-Aufruf (falls nicht vom Solver gelöst)
  OAI --> SB : Antwort + usage
  SB --> CLI : Pipeline-Output (JSON)
  CLI --> Eval : result.json
  Eval -> Eval : Format exakt [ABCD]? richtig? Tokens? Zeit?
end
Eval --> Dev : x/N richtig · Tokens/Frage · Fehlerliste
alt Genauigkeit gleich oder besser und weniger Tokens
  Dev -> CLI : deploy agent.py quiz
else
  Dev -> Dev : verwerfen, nächste Hypothese
end
@enduml
```

![eval-loop](diagrams/eval-loop.svg)

### 4.3 Agenten-Duell im Frontend

```plantuml
@startuml frontend-duel
!theme plain
skinparam shadowing false
title Vinland Pub Quiz · Mensch gegen 8 KI-Modelle

actor "Team Vinland" as Team
participant "index.html\n(Knut + 9 Spieler)" as UI
participant "server.py" as Srv
participant "8 KI-Spieler\n(je ein Modell)" as A1

Team -> UI : „Segel setzen“
UI -> UI : Musik + Kriegshorn
UI -> Srv : GET /api/questions
Srv --> UI : 1060 Fragen + 8 Modelle
loop jede Frage
  UI -> UI : Trommel, Knut stellt die Frage
  par 8 KI-Spieler gleichzeitig
    UI -> Srv : 8× POST /api/ask {agent: <Modell>}
    Srv -> A1 : Sandbox-Run oder Live-Service
    A1 --> Srv : "D", Tokens, Sekunden
    Srv --> UI : letter, tokens, seconds
  else Mensch
    Team -> UI : Taste A–D (👤 Mensch)
  end
  Team -> UI : Auflösen
  UI -> UI : Schwertklang, Markierung der Optionen,\nSprechblasen, Jubel oder Stöhnen
end
UI -> UI : Rekordleiste (führt / günstigste / schnellste KI),\nPodium nach Leaderboard-Regeln + Siegesfest
@enduml
```

![frontend-duel](diagrams/frontend-duel.svg)

## 5. Eval-Ergebnisse

### 5.1 Iterationen auf 60 eigenen Fragen (40 normal + 20 schwer)

| # | Variante | Richtig | Tokens/Frage | Erkenntnis |
|---|---|---|---|---|
| 0 | Starter: gpt-5.1 + `calculate` + `count_letter` | 39/40 | 460 | Tool-Schemas bei jeder Frage, Tool-Aufruf = zweiter LLM-Call |
| 1 | gpt-4.1, kein Prompt, `logit_bias` A–D, 1 Token | 28/40 | 38 | ohne Anweisung tippt das Modell meist „A“ |
| 2 | gpt-5.1 ohne Tools, Kurzprompt | 34/40 | 58 | Arithmetik scheitert ohne Nachdenken |
| 2 | `max_completion_tokens: 1` bei gpt-5.x | 0/40 | – | HTTP 400, die Obergrenze ist ohnehin nur ein Deckel |
| 3 | **gpt-5.4, `reasoning_effort: low`, keine Tools** | **40/40** | **66** | Denken ersetzt Tools, Tokens nur wo nötig |
| 3 | gpt-5.4 nur mit `calculate` | 37/40 | 274 | Tool kostet und lieferte teils leere Antworten |
| 4 | Prompt „Letter only.“ | 39/40 | 68 | antwortete einmal „C) Carbon dioxide“ → zurück zum 7-Wort-Prompt |
| 5 | **Pipeline: QuickAnswer → Agent → BranchJoiner** | **60/60** | **46 / 52** | 17 von 60 Fragen mit 0 Tokens, −33 % gegenüber Iteration 3 |

### 5.2 1000 Fragen aus The Trivia API (47 % schwer, 10 Kategorien)

| Agent | Richtig | Tokens/Frage | Anmerkung |
|---|---|---|---|
| **quiz** (gpt-5.4, Pipeline) | **993/1000** | 76 | 0 Formatfehler; 1 Fehler war ein Plattform-Aussetzer (502), 1 „Fehler“ ist ein Fehler im Datensatz (Dromedar: 0 statt 1 Höcker) |
| Luna-Fork (wie auf der Plattform angelegt) | 1/1000 | 68 | 999 Formatfehler wie „D) Inception“; der Buchstabe am Anfang stimmte 962-mal: Wissen da, Format kaputt |
| **Luna repariert** (`agent_luna.py`) | **993/1000** | **61** | 0 Formatfehler; gleiche Pipeline, nur Modell getauscht: **−19 % Tokens bei gleicher Genauigkeit** |

Je drei Fragen konnte nur gpt-5.4 bzw. nur Luna richtig beantworten; die übrigen Fehler teilen sich beide Modelle und
betreffen überwiegend fragwürdige Lösungen im Datensatz (Dromedar-Höcker, Erfindungsjahr der CD). **Bei Gleichstand der
richtigen Antworten gewinnt nach den Regeln Luna, weil es 19 % weniger Tokens braucht.**

### 5.3 Acht Modelle, gleiche Pipeline, gleiche Fragen

Die vollständige Tabelle mit Genauigkeit und isolierter Geschwindigkeit pro Agent: [`evals/RESULTS.md`](../evals/RESULTS.md)
(neu erzeugen: `uv run python evals/summarize.py`). Isoliert gemessen ist gpt-5.4-mini mit 3,0 s auch das schnellste der genauesten Modelle.

Alle Modelle laufen in derselben Pipeline (Solver + Agent), jeweils mit ihrer besten Einstellung: Reasoning-Modelle mit
`reasoning_effort: low`, gpt-4.1/gpt-4o-mini mit 1 Token und `logit_bias` auf A–D (sonst antworten sie „C) 87.5%“).

| Modell | Trivia 200 (hohe Last) | Eigene 60 (geringe Last) | Median-Zeit (geringe Last) | Tokens/Frage (eigene 60) |
|---|---|---|---|---|
| **gpt-5.4-mini** | **200** | **59** | **10,4 s** | 49 |
| gpt-5.4 | 199 | 59 | 10,7 s | 49 |
| gpt-5.1 | 200 | 59 | 10,8 s | 48 |
| gpt-5-mini | 199 | 59 | 11,4 s | 50 |
| gpt-4.1 | 199 | 57 | 10,0 s | 36 |
| gpt-5.6-luna | 197 | 57 | 11,1 s | 39 |
| gpt-4o-mini | 195 | 55 | 10,0 s | 36 |
| gpt-5.4-nano | 191 | 58 | 10,8 s | 48 |

- Die Zeiten enthalten den Sandbox-Start (~8–10 s); Unterschiede zwischen den Modellen liegen bei Zehntelsekunden.
  Unter hoher Last (48 parallele Läufe) waren Luna und gpt-5.4 im Paarvergleich gleich schnell (Median-Differenz 0,02 s).
- gpt-4.1 und gpt-4o-mini sind am schnellsten und günstigsten, verlieren aber bei Textaufgaben (Zug, Wechselgeld, Datumsrechnung)
  2–5 Punkte. Bei „genau vor schnell“ scheiden sie aus; in einer 5-Fragen-Runde nur mit Wissensfragen gewinnen sie trotzdem.
- **Entscheidung (Ziel: genau, dann schnell): `quiz` läuft seit 20:22 auf gpt-5.4-mini** — am genauesten und unter den
  genauen Modellen am schnellsten. `quiz-luna` bleibt als reparierte Luna-Variante.
- Live gemessen: nach frischem Deploy (Kaltstart) 10–18 s, warm unter 2 s. **Vor dem Quiz aufwärmen ist Pflicht.**

## 6. Der Luna-Fix

Der Fork `quiz-cf5ea67e-fork` (Service `quiz-luna`) übernahm die Pipeline, verlor aber beim Modellwechsel im Builder den
Systemprompt und alle `generation_kwargs`. Folgen: Luna antwortete in ganzen Sätzen, und gestreamte Antworten meldeten keine Tokens.
Der Fix ist [`agent_luna.py`](../agent_luna.py): `build_pipeline("gpt-5.6-luna")` aus [`agent.py`](../agent.py), deployt als neue
Revision von `quiz-luna`. So bleiben beide Agenten identisch bis auf das Modell, und ein Vergleich misst wirklich nur das Modell.

## 7. Risiken und offene Punkte

- **Sandbox-Warteschlange:** Ein Lauf allein dauert 2–4 s, drei gleichzeitig 6–14 s. Das Frontend lässt die 8 KIs deshalb nacheinander laufen (`SANDBOX_PARALLEL=1`).
- **Kaltstart:** Serverless-Services gehen in „Standby“; die erste Frage kann 6–16 s brauchen (Limit 15 s). Kurz vor dem Quiz eine Frage senden.
- **Token-Zählung bei 0-Token-Antworten:** Wie das Leaderboard Antworten ohne LLM-Aufruf (fehlendes `usage`) wertet, ist nicht bestätigt.
- **Datensatzfehler:** Öffentliche Trivia-Sets enthalten falsche Lösungen; 99 %+ ist nahe an der Messgrenze.
- **Fragen vorab beschaffen** wäre Schummeln und ist nicht Teil der Strategie; der Solver rechnet nur, was sich aus der Frage selbst ergibt.

## 8. So läuft alles

```bash
uv sync
uv run python check.py                                   # 3 Beispielfragen in der Sandbox
QZ_SET=trivia/questions_trivia.json QZ_TAG=_trivia uv run python evals/run_eval.py p1_pipeline
haystack-enterprise deploy agent.py quiz                 # gpt-5.4
haystack-enterprise deploy agent_luna.py quiz-luna --io-config agent.io.yaml
uv run python frontend/make_sounds.py                    # ElevenLabs (CLI oder ELEVEN_LABS_API_KEY aus .env), einmalig
uv run python frontend/server.py                         # http://localhost:8765
```
