# LinkedIn-Post · deepset Haystack Enterprise Hack Night

Veröffentlicht von Matthias Buchhorn-Roth am Morgen nach der Hack Night (22. Oktober 2026).
Dazu passend: das Video aus [`video/`](../video/SCREENPLAY.md) und das Online-Quiz unter
[ma3u.github.io/hacknight](https://ma3u.github.io/hacknight/).

---

Tonight deepset, makers of Haystack opened its Berlin office for the #Haystack Enterprise Platform (HEP) Hack Night,
part of the "House of Sovereignty" program during #NVIDIAGTCBerlin.

The challenge: build the fastest and most accurate agent for a pub quiz. More than 35 teams sent their agents into
battle.

My daughter and I started to develop a game to test and evaluate various agents:
⚔️ 1 human vs. 7 AI agents: a Viking pub quiz on the way to Vinland

What surprised us:
🏆 The heavily optimized pipelines didn't win. The newest and biggest model did (OpenAI Astra).
🔎 Places 2 and 3 went to agents with web search. Some quiz questions can't be answered from model weights alone.

🧑 Our twist: we screen-recorded the run and let the human take over from Opus 5.5.

My takeaways for agentic AI in enterprise and the public sector:

1️⃣ Model choice is still the biggest lever. You pay for it in cost, latency and, for sovereign setups, dependency.
2️⃣ Grounding beats prompt tuning. If the knowledge isn't in the model, give the agent a way to find it.
3️⃣ Use objective evaluation on real data before you optimize anything.
4️⃣ It was fitting that this happened in a "House of Sovereignty." The real challenge is getting this performance with
models and infrastructure we control in Europe.

Bonus: the HEP workspaces stay open for another week, so the Vikings will sail again. 🛶

Thank you Bilge Yücel and the deepset team (Jay Wilder, Luke Walker, Dr. Anna Gründler, Paula Plattner) for a wonderful
evening, great mentors and good food.

#Haystack #deepset #NVIDIAGTC #GTCBerlin #AgenticAI #MultiAgentSystems #SovereignAI #RAG #HackNight #Berlin

---

## Was seitdem passiert ist

„The Vikings will sail again“: Die Gewinner-Strategien aus dem Post sind inzwischen nachgebaut und gemessen
(Details in [`IMPROVEMENTS.md`](IMPROVEMENTS.md), Abschnitt 4, und [`STRATEGY.md`](STRATEGY.md), Abschnitt 5.4):

- **Websuche (Takeaway 2):** Ein Router schickt Fragen zu aktuellen Ereignissen an einen Agent mit OpenAI-Websuche.
  Auf 14 belegten Fragen zu Juli–Oktober 2026: 14/14 statt 4/14, normale Fragen bleiben schlank.
- **Größtes Modell (Takeaway 1):** GPT-6 Astra kennt 7 der 14 aktuellen Ereignisse und ist bei normalen Fragen
  genauso genau, wird mit Websuche aber zu langsam fürs 15-Sekunden-Limit. Gewählt: gpt-5.4-mini mit Suche.
- **Evaluation (Takeaway 3):** Ohne den Blick in die Agent-Nachrichten hätten wir eine kaputte Suche (HTTP 403)
  für „Suche bringt wenig“ gehalten.
