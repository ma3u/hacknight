# Drehbuch · Vinland Pub Quiz (LinkedIn, 75 s, 1080×1350)

Aufnahme:
- LinkedIn-Feed (4:5, 1080×1350): `uv run --with playwright python video/record_video.py` → `video/out/vinland-quiz-linkedin.mp4`
- Desktop (16:9, 1920×1080, Animation rund um das Quiz sichtbar): `uv run --with playwright python video/record_video.py desktop`
  → `video/out/vinland-quiz-desktop.mp4`
Gespielt wird die Online-Version (Replay) in Google Chrome; die acht KI-Modelle antworten mit ihren echten,
aufgezeichneten Eval-Antworten. **Den Menschen spielt Claude Opus 5.5**: Die fünf Antworten hat Opus 5.5 vor der
Aufnahme selbst gewählt; das Skript tippt sie nach 2–3,5 s „Bedenkzeit“ ein. Ton: ElevenLabs-Musik, -Effekte und
Knuts Stimme, zeitgenau aus dem Sound-Log der Seite gemischt.

| Zeit | Szene | Bild | Ton | Einblendung |
|---|---|---|---|---|
| 0:00 | Titel | Titelkarte über dem Setup | – | „Vinland Pub Quiz · 1 Mensch gegen 8 KI-Modelle · Den Menschen spielt Claude Opus 5.5“ |
| 0:04 | Aufstellung | Knut erklärt die Regeln, 8 Figuren mit ihren Modellen | – | „Gleiche Haystack-Pipeline für alle: QuickAnswer-Solver → Agent → BranchJoiner“ |
| 0:08 | Segel setzen | Quiz startet, Rekordleiste erscheint | Musik, Kriegshorn, Knut: „Hört mich an, Krieger von Vinland!“ | – |
| 0:10 | Frage 1: 17 × 23 | Opus wählt B; alle KIs mit **0 Tokens** (Solver) | Schwert, Jubel, Knut: „Richtig! Skål!“ | „Rechenfrage: der Solver rechnet in Python. 0 Tokens, kein LLM-Aufruf.“ |
| 0:20 | Frage 2: Zug 300 km / 2,5 h | gpt-5.4-nano, gpt-5.1, gpt-4.1, gpt-4o-mini liegen falsch | Trommel, Schwert, Jubel, Knut | „Textaufgabe: hier trennt sich die Spreu vom Weizen.“ |
| 0:31 | Frage 3: „This beat is automatic…“ | Luna, gpt-5.4, nano greifen daneben | Trommel, Schwert, Jubel, Knut | „Musikwissen: selbst große Modelle greifen daneben.“ |
| 0:42 | Frage 4: Tage 1. Jan → 1. März | Luna, gpt-4.1, gpt-4o-mini verrechnen sich | Trommel, Schwert, Jubel, Knut | „Datumsrechnung: wer denkt kurz nach?“ |
| 0:52 | Frage 5: Batman Begins & Lucy | nano, gpt-4.1, gpt-4o-mini verwechseln Morgan Freeman | Trommel, Schwert, Jubel, Knut | „Filmwissen zum Finale.“ |
| 1:02 | Ergebnis | Podium: #1 gpt-5.4-mini, #2 gpt-5-mini, #3 Opus 5.5 (alle 5/5; Tokens entscheiden) | Siegesfest | „Sieger nach ‚genau, dann schnell‘: gpt-5.4-mini · 99,6 % · 3,0 s, live im Service quiz“ |
| 1:09 | Abspann | Abspannkarte | Musik | „Skål! · Selbst spielen: ma3u.github.io/hacknight · Code: github.com/ma3u/hacknight“ |

## LinkedIn-Post (Vorschlag)

> ⚔️ Mensch gegen Maschine, im Wikinger-Stil.
>
> Beim deepset Hacknight haben wir als Team Vinland einen Quiz-Agenten auf der Haystack Enterprise Platform gebaut:
> so genau wie möglich, dann so schnell wie möglich, mit möglichst wenigen Tokens.
>
> Was den Unterschied gemacht hat:
> 🧮 Ein Python-Solver beantwortet Rechen- und Zählfragen mit 0 Tokens, bevor überhaupt ein LLM gefragt wird
> 🧠 reasoning_effort „low“ statt Tools: Tokens nur dort, wo nachgedacht werden muss (−90 % gegenüber dem Starter-Agent)
> 📊 8 OpenAI-Modelle in derselben Pipeline, gemessen auf 1.000 Pub-Quiz-Fragen: gpt-5.4-mini gewinnt mit 99,6 % und 3,0 s
>
> Im Video tritt Claude Opus 5.5 als „Mensch“ gegen alle acht Modelle an, mit Knut dem Großen als Quizmaster.
> Musik, Kriegshorn und Stimmen: ElevenLabs.
>
> Selbst spielen: https://ma3u.github.io/hacknight
> Code & Strategie: https://github.com/ma3u/hacknight
>
> #Haystack #deepset #AIAgents #LLM #Hackathon #ElevenLabs
