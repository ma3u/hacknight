# LinkedIn post · deepset Haystack Enterprise Hack Night

Published by Matthias Buchhorn-Roth the morning after the Hack Night (October 22, 2026):
**[read the post on LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7518778597650673665/)**

Related: the video in [`video/`](../video/SCREENPLAY.md) and the online quiz at
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

## What happened since

"The Vikings will sail again": the winners' strategies from the post have since been rebuilt and measured
(details in [`IMPROVEMENTS.md`](IMPROVEMENTS.md), stage 4, and [`STRATEGY.md`](STRATEGY.md), section 5.4):

- **Web search (takeaway 2):** a router sends questions about recent events to an agent with OpenAI web search.
  On 14 sourced questions about July–October 2026: 14/14 instead of 4/14, while normal questions stay lean.
- **Biggest model (takeaway 1):** GPT-6 Astra knows 7 of the 14 recent events and is just as accurate on normal
  questions, but with web search it's too slow for the 15-second limit. Chosen: gpt-5.4-mini with search.
- **Evaluation (takeaway 3):** without looking at the agent's messages we would have mistaken a broken search
  (HTTP 403) for "search doesn't help much".
