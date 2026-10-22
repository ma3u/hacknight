# Screenplay · Vinland Pub Quiz (LinkedIn, 75 s, 1080×1350)

Recording:
- LinkedIn feed (4:5, 1080×1350): `uv run --with playwright python video/record_video.py` → `video/out/vinland-quiz-linkedin.mp4`
- Desktop (16:9, 1920×1080, with the animation visible around the quiz): `uv run --with playwright python video/record_video.py desktop`
  → `video/out/vinland-quiz-desktop.mp4`

The recording plays the online version (replay) in Google Chrome; the AI agents answer with their real, recorded eval
answers. **Claude Opus 5.5 plays the human**: Opus 5.5 chose its five answers before the recording, and the script types
them after 2–3.5 s of "thinking time". Sound: ElevenLabs music, effects and Cnut's voice, mixed in sync from the page's
sound log.

| Time | Scene | Picture | Sound | Caption |
|---|---|---|---|---|
| 0:00 | Title | title card over the setup screen | – | "Vinland Pub Quiz · 1 human vs. AI agents · The human is played by Claude Opus 5.5" |
| 0:04 | Line-up | Cnut explains the rules, the characters with their models | – | "Same Haystack pipeline for all: QuickAnswer solver → agent → BranchJoiner" |
| 0:08 | Set sail | the quiz starts, the records bar appears | music, war horn, Cnut's welcome | – |
| 0:10 | Question 1: 17 × 23 | Opus picks B; all AIs with **0 tokens** (solver) | sword, cheers, Cnut: "Correct!" | "Arithmetic: the solver computes it in Python. 0 tokens, no LLM call." |
| 0:20 | Question 2: train 300 km / 2.5 h | gpt-5.4-nano, gpt-5.1, gpt-4.1, gpt-4o-mini get it wrong | drum, sword, cheers, Cnut | "Word problem: this is where the models split." |
| 0:31 | Question 3: "This beat is automatic…" | Luna, gpt-5.4, nano miss it | drum, sword, cheers, Cnut | "Music knowledge: even big models miss." |
| 0:42 | Question 4: days Jan 1 → Mar 1 | Luna, gpt-4.1, gpt-4o-mini miscount | drum, sword, cheers, Cnut | "Date arithmetic: who thinks for a moment?" |
| 0:52 | Question 5: Batman Begins & Lucy | nano, gpt-4.1, gpt-4o-mini miss Morgan Freeman | drum, sword, cheers, Cnut | "Film knowledge for the finale." |
| 1:02 | Result | podium: #1 gpt-5.4-mini, #2 gpt-5-mini, #3 Opus 5.5 (all 5/5; tokens decide) | victory feast | "Winner under 'accurate, then fast': gpt-5.4-mini · 99.6 % · 3.0 s, live in the quiz service" |
| 1:09 | Closing | closing card | music | "Skål! · Play it: ma3u.github.io/hacknight · Code: github.com/ma3u/hacknight" |

The post that went with the video: [`docs/LINKEDIN.md`](../docs/LINKEDIN.md)
([on LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7518778597650673665/)).
