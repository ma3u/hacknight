"""Record the LinkedIn video of the Vinland pub quiz: uv run --with playwright python video/record_video.py

A scripted screen recording (the screenplay is SCENES below) of the static quiz build in Google Chrome,
captured with the DevTools screencast at 1.5x pixel density (crisp 1080x1350 frames from a 720x900 layout):
the human player is simulated with answers Claude Opus 5.5 chose for these questions before recording,
the eight AI models replay their recorded eval answers. Browser video has no audio, so every sound the page
plays is logged with its timestamp and the same ElevenLabs files are mixed onto the video with ffmpeg.

Output: video/out/vinland-quiz-linkedin.mp4 (1080x1350, 4:5 for the LinkedIn feed).
"""

import asyncio
import base64
import functools
import http.server
import json
import random
import shutil
import subprocess
import threading
import time
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
OUT = Path(__file__).resolve().parent / "out"
VIEWPORT = {"width": 720, "height": 900}  # rendered at 1.5x: same 1080x1350 file, 50 % larger, crisp text for phones
SIZE = {"width": 1080, "height": 1350}
PORT = 8767
ROUND = "4,30,129,37,249"
HUMAN = "Opus 5.5"

# The screenplay: per question, the caption shown and the answer Opus 5.5 gives as the human player.
SCENES = [
    ("Szene 1 · Rechenfrage: der Solver rechnet in Python. 0 Tokens, kein LLM-Aufruf.", "b"),
    ("Szene 2 · Textaufgabe: hier trennt sich die Spreu vom Weizen.", "c"),
    ("Szene 3 · Musikwissen: selbst große Modelle greifen daneben.", "c"),
    ("Szene 4 · Datumsrechnung: wer denkt kurz nach?", "b"),
    ("Szene 5 · Filmwissen zum Finale.", "d"),
]

OVERLAY = """
() => {
  const css = document.createElement('style');
  css.textContent = `
    #rec-card { position: fixed; inset: 0; z-index: 1000; display: grid; place-content: center; text-align: center; gap: 18px;
      background: radial-gradient(circle at 50% 40%, rgba(20,40,80,.96), rgba(5,7,15,.98)); color: #efe6d2; transition: opacity .8s;
      font-family: Inter, sans-serif; padding: 40px; }
    #rec-card h1 { font: 900 46px/1.05 "Cinzel Decorative", serif; margin: 0; text-shadow: 4px 4px 0 #05070f; }
    #rec-card .kick { font: 700 15px/1.3 Cinzel, serif; letter-spacing: .3em; text-transform: uppercase; color: #e4b04a; }
    #rec-card .sub { font: 600 22px/1.35 Inter; }
    #rec-card .small { font: 500 17px/1.4 Inter; color: #b9b09c; }
    #rec-cap { position: fixed; left: 24px; right: 24px; bottom: 24px; z-index: 999; padding: 18px 24px; border-radius: 14px;
      background: rgba(5,7,15,.88); border: 2px solid #e4b04a; color: #efe6d2; font: 700 19px/1.3 Inter; text-align: center;
      box-shadow: 6px 6px 0 #05070f; transition: opacity .4s; opacity: 0; }`;
  document.head.appendChild(css);
  window.recCard = (html, show) => {
    let el = document.getElementById('rec-card');
    if (!el) { el = document.createElement('div'); el.id = 'rec-card'; document.body.appendChild(el); }
    if (html) el.innerHTML = html;
    el.style.opacity = show ? 1 : 0; el.style.pointerEvents = show ? 'auto' : 'none';
  };
  window.recCaption = (text) => {
    let el = document.getElementById('rec-cap');
    if (!el) { el = document.createElement('div'); el.id = 'rec-cap'; document.body.appendChild(el); }
    if (text) el.textContent = text;
    el.style.opacity = text ? 1 : 0;
  };
}
"""

# Log every sound the page starts (src, volume, wall-clock time) so ffmpeg can mix them in sync.
SOUND_LOG = """
try { localStorage.setItem('vinland-sound', 'on'); } catch {}
window.__soundLog = [];
const play = HTMLMediaElement.prototype.play;
HTMLMediaElement.prototype.play = function () {
  window.__soundLog.push({ t: Date.now(), src: this.src.split('/').pop(), volume: this.volume, loop: this.loop });
  return play.call(this);
};
"""


def serve() -> http.server.ThreadingHTTPServer:
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=str(SITE)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


async def record() -> tuple[Path, list, float, float]:
    """Drive Chrome through the screenplay and capture it with the DevTools screencast at full pixel density."""
    shutil.rmtree(OUT / "frames", ignore_errors=True)
    (OUT / "frames").mkdir(parents=True)
    server = serve()
    frames: list[tuple[float, Path]] = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome", args=["--autoplay-policy=no-user-gesture-required"])
        context = await browser.new_context(viewport=VIEWPORT, device_scale_factor=1.5)
        await context.add_init_script(SOUND_LOG)
        page = await context.new_page()
        cdp = await context.new_cdp_session(page)

        async def on_frame(params):
            path = OUT / "frames" / f"{len(frames):06d}.jpg"
            path.write_bytes(base64.b64decode(params["data"]))
            frames.append((params["metadata"]["timestamp"], path))
            await cdp.send("Page.screencastFrameAck", {"sessionId": params["sessionId"]})

        cdp.on("Page.screencastFrame", lambda params: asyncio.ensure_future(on_frame(params)))
        await page.goto(f"http://127.0.0.1:{PORT}/?round={ROUND}&human={HUMAN.replace(' ', '%20')}")
        await page.wait_for_function("document.querySelectorAll('#lineup .fighter').length === 8")
        await page.evaluate(OVERLAY)
        await page.evaluate("""recCard(`<div class="kick">deepset Hacknight · Haystack Enterprise</div>
            <h1>Vinland Pub Quiz</h1><div class="sub">1 Mensch gegen 8 KI-Modelle</div>
            <div class="small">Den Menschen spielt Claude Opus 5.5 · Team Vinland</div>`, true)""")
        await page.wait_for_timeout(300)
        await cdp.send("Page.startScreencast", {"format": "jpeg", "quality": 92, "maxWidth": SIZE["width"], "maxHeight": SIZE["height"]})
        await page.wait_for_timeout(4000)
        await page.evaluate("recCard(null, false)")
        await page.evaluate("recCaption('Gleiche Haystack-Pipeline für alle: QuickAnswer-Solver → Agent → BranchJoiner')")
        await page.wait_for_timeout(3500)
        await page.evaluate("recCaption('')")
        await page.click("#start")
        await page.wait_for_timeout(1500)

        for caption, letter in SCENES:
            await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
            await page.evaluate("t => recCaption(t)", caption)
            await page.wait_for_timeout(int(random.uniform(2200, 3400)))  # Opus 5.5 "thinks"
            await page.keyboard.press(letter)
            await page.wait_for_function("!document.getElementById('reveal').disabled", timeout=30000)
            await page.wait_for_timeout(700)
            await page.click("#reveal")
            await page.wait_for_timeout(1400)
            await page.evaluate("document.getElementById('arena').scrollIntoView({ behavior: 'smooth', block: 'start' })")
            await page.wait_for_timeout(3600)
            await page.evaluate("recCaption('')")
            await page.click("#next")
            await page.wait_for_timeout(600)

        await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
        await page.evaluate("recCaption('Sieger nach „genau, dann schnell“: gpt-5.4-mini · 99,6 % · 3,0 s, live im Service quiz')")
        await page.wait_for_timeout(4500)
        await page.evaluate("document.getElementById('podium').scrollIntoView({ behavior: 'smooth', block: 'start' })")
        await page.wait_for_timeout(2500)
        await page.evaluate("recCaption('')")
        await page.evaluate("""recCard(`<div class="kick">Team Vinland</div><h1>Skål!</h1>
            <div class="sub">Gebaut mit Haystack Enterprise, 8 OpenAI-Modellen und ElevenLabs</div>
            <div class="small">Selbst spielen: ma3u.github.io/hacknight<br>Code: github.com/ma3u/hacknight</div>`, true)""")
        await page.wait_for_timeout(5000)
        end_ts = time.time()
        await cdp.send("Page.stopScreencast")
        await page.wait_for_timeout(300)
        sounds = await page.evaluate("window.__soundLog")
        await browser.close()
    server.shutdown()

    # Variable-rate screencast frames -> constant 30 fps video, timed by the frames' own timestamps.
    frames.sort()
    t0 = frames[0][0]
    concat = OUT / "frames.txt"
    lines = ["ffconcat version 1.0"]
    for (ts, path), nxt in zip(frames, [f[0] for f in frames[1:]] + [end_ts]):
        lines += [f"file '{path}'", f"duration {max(nxt - ts, 0.001):.4f}"]
    lines.append(f"file '{frames[-1][1]}'")
    concat.write_text("\n".join(lines) + "\n")
    video = OUT / "video_only.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(concat), "-vf",
                    f"fps=30,scale={SIZE['width']}:{SIZE['height']}:flags=lanczos", "-c:v", "libx264", "-preset", "slow",
                    "-crf", "18", "-pix_fmt", "yuv420p", str(video)], check=True)
    return video, sounds, t0 * 1000, (end_ts - t0) * 1000


def mix(video: Path, sounds: list, t0: float, duration: float) -> Path:
    """Put the logged sounds onto the video timeline; the music loops from its start to the end."""
    out = OUT / "vinland-quiz-linkedin.mp4"
    inputs, filters, labels = ["-i", str(video)], [], []
    for n, s in enumerate(s for s in sounds if s["src"].endswith(".mp3")):
        delay = max(0, int(s["t"] - t0))
        src = SITE / "sounds" / s["src"]
        if s["loop"]:
            inputs += ["-stream_loop", "-1", "-i", str(src)]
        else:
            inputs += ["-i", str(src)]
        idx = n + 1
        filters.append(f"[{idx}]adelay={delay}|{delay},volume={max(s['volume'], .2):.2f}[a{idx}]")
        labels.append(f"[a{idx}]")
    filters.append(f"{''.join(labels)}amix=inputs={len(labels)}:normalize=0,atrim=0:{duration / 1000:.2f},alimiter=limit=0.95[aout]")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *inputs, "-filter_complex", ";".join(filters),
                    "-map", "0:v", "-map", "[aout]", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", f"{duration / 1000:.2f}", str(out)],
                   check=True)
    (OUT / "sound_log.json").write_text(json.dumps([dict(s, at_ms=int(s["t"] - t0)) for s in sounds], indent=1))
    return out


if __name__ == "__main__":
    if not (SITE / "index.html").exists():
        subprocess.run(["python3", str(ROOT / "frontend" / "build_static.py"), str(SITE)], check=True)
    video, sounds, t0, duration = asyncio.run(record())
    print(f"recorded {duration / 1000:.1f}s, {len(sounds)} sounds")
    print(f"✅ {mix(video, sounds, t0, duration)}")
