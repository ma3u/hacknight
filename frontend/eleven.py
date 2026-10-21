"""ElevenLabs access for the quiz frontend: the `elevenlabs` CLI when installed, else the REST API.

The REST path reads ELEVEN_LABS_API_KEY (or ELEVENLABS_API_KEY) from the environment or the repo's .env
(gitignored). The key is only ever sent to api.elevenlabs.io; nothing here prints it.
"""

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = shutil.which("elevenlabs")
API = "https://api.elevenlabs.io/v1"
KEY_NAMES = ("ELEVEN_LABS_API_KEY", "ELEVENLABS_API_KEY")
MODEL = os.environ.get("ELEVEN_MODEL", "eleven_v4")
FALLBACK_MODEL = "eleven_multilingual_v2"
FALLBACK_VOICE = "JBFqnCBsd6RMkjVDRZzb"  # George, a premade voice every account has


def api_key() -> str:
    for name in KEY_NAMES:
        if os.environ.get(name):
            return os.environ[name]
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            name, _, value = line.strip().removeprefix("export ").partition("=")
            if name.strip() in KEY_NAMES:
                return value.strip().strip("\"'")
    return ""


def available() -> bool:
    return bool(CLI or api_key())


def _cli(*args: str) -> None:
    run = subprocess.run([CLI, *args], capture_output=True, text=True, timeout=180)
    if run.returncode != 0:
        raise RuntimeError((run.stdout + run.stderr)[-300:])


def _post(path: str, body: dict, out: Path) -> None:
    request = urllib.request.Request(API + path, data=json.dumps(body).encode(), method="POST", headers={
        "xi-api-key": api_key(), "Content-Type": "application/json", "Accept": "audio/mpeg"})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            out.write_bytes(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"ElevenLabs {error.code}: {error.read()[:300].decode(errors='replace')}") from None


def sound_effect(text: str, out: Path, seconds: float | None = None) -> None:
    if CLI:
        return _cli("text-to-sound-effects", "convert", "--text", text, "--output", str(out))
    body = {"text": text, "prompt_influence": 0.5}
    if seconds:
        body["duration_seconds"] = seconds
    _post("/sound-generation", body, out)


def speech(text: str, voice: str, out: Path) -> None:
    """Text to speech; falls back to a premade voice and a widely available model if the account lacks them."""
    attempts = [(voice, MODEL), (voice, FALLBACK_MODEL), (FALLBACK_VOICE, FALLBACK_MODEL)]
    error = None
    for v, model in dict.fromkeys(attempts):
        try:
            if CLI:
                return _cli("text-to-speech", "convert", "--voice-id", v, "--model-id", model, "--text", text,
                            "--output-format", "mp3_44100_128", "--output", str(out))
            return _post(f"/text-to-speech/{v}?output_format=mp3_44100_128", {"text": text, "model_id": model}, out)
        except RuntimeError as e:
            error = e
    raise error


def music(prompt: str, out: Path, seconds: int = 90) -> None:
    if CLI:
        return _cli("music", "compose", "--prompt", prompt, "--music-length-ms", str(seconds * 1000), "--output", str(out))
    _post("/music", {"prompt": prompt, "music_length_ms": seconds * 1000}, out)
