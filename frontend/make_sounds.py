"""Generate the Vinland pub quiz soundscape and voice lines with ElevenLabs into frontend/sounds/.

uv run python frontend/make_sounds.py [--force]

Uses the `elevenlabs` CLI when installed (`elevenlabs auth login`), else the REST API with
ELEVEN_LABS_API_KEY from .env. Each file costs credits once; existing files are skipped. The frontend
uses whatever exists and synthesizes the rest. Override voices with KNUT_VOICE, WARRIOR_VOICE, SHIELDMAIDEN_VOICE.
"""

import os
import sys
from pathlib import Path

import eleven

OUT = Path(__file__).resolve().parent / "sounds"
KNUT = os.environ.get("KNUT_VOICE", "JBFqnCBsd6RMkjVDRZzb")                  # George: deep, warm -> king and quizmaster
WARRIOR = os.environ.get("WARRIOR_VOICE", "2EiwWnXFnvU5JabPnv8n")            # Clyde: gravelly veteran -> warriors
SHIELDMAIDEN = os.environ.get("SHIELDMAIDEN_VOICE", "AZnzlk1XvdvUeBnXmlld")  # Domi: strong, fierce -> shieldmaidens

MUSIC = ("Epic Nordic Viking folk music for a pub quiz night: deep frame drums and taiko, low throat-singing drones, "
         "tagelharpa and hurdy-gurdy melody, crackling hearth, steady mid tempo, adventurous but calm enough to think, "
         "instrumental, no lyrics, seamless loop")
MUSIC_LOOP = ("Seamless loop of cinematic Nordic Viking ambience: slow frame drums, deep throat-singing drone, "
              "tagelharpa melody, fire crackling in a longhouse")

EFFECTS = {
    "horn": ("Cinematic Viking war horn: one deep, long lur horn blast echoing across a misty fjord, distant reverb", 5),
    "drum": ("Two heavy Viking war drum hits followed by warriors striking wooden shields once, punchy, close", 2),
    "reveal": ("A steel sword drawn slowly from a leather scabbard, bright metallic ring at the end", 2),
    "cheer": ("A Viking village crowd erupts in cheers, men and women shouting Skål, wooden mugs clinking, triumphant", 3),
    "groan": ("A Viking longhouse crowd groans in disappointment, ohhh, a few mocking laughs", 2.5),
    "victory": ("Huge Viking village victory feast: crowd chanting and stomping in rhythm, war horns and drums, roaring celebration", 7),
}
VOICES = {
    "knut_start": (KNUT, "Hört mich an, Krieger von Vinland! Das Quiz beginnt. Möge Odin euren Verstand schärfen!"),
    "knut_right": (KNUT, "Richtig! Skål!"),
    "knut_some": (KNUT, "Einige von euch wissen es. Die anderen rudern morgen."),
    "knut_nobody": (KNUT, "Keiner?! Schande über euch alle!"),
    "knut_victory": (KNUT, "Vinland ist erobert! Feiert, Wikinger, der Met fließt heute Nacht!"),
    "warrior_win": (WARRIOR, "Skål! Für Vinland!"),
    "warrior_lose": (WARRIOR, "Bei Odins Bart… verflucht!"),
    "shieldmaiden_win": (SHIELDMAIDEN, "Wie ein Speer ins Ziel!"),
    "shieldmaiden_lose": (SHIELDMAIDEN, "Thor, warum?!"),
}


def make(name: str, build) -> bool:
    path = OUT / f"{name}.mp3"
    if path.exists() and "--force" not in sys.argv:
        print(f"⏭  {name}.mp3 exists")
        return True
    try:
        build(path)
        print(f"✅ {name}.mp3 ({path.stat().st_size // 1024} KB)")
        return True
    except Exception as error:  # report and keep going: one missing file only means a synth stand-in
        path.unlink(missing_ok=True)
        print(f"❌ {name}.mp3: {error}")
        return False


def main() -> int:
    if not eleven.available():
        print("❌ No ElevenLabs access: install the CLI (brew install elevenlabs/tap/elevenlabs) or set ELEVEN_LABS_API_KEY in .env")
        return 1
    OUT.mkdir(exist_ok=True)
    print(f"Using the ElevenLabs {'CLI' if eleven.CLI else 'REST API'}")
    if not make("music", lambda p: eleven.music(MUSIC, p)):
        make("music", lambda p: eleven.sound_effect(MUSIC_LOOP, p, 22))
    for name, (prompt, seconds) in EFFECTS.items():
        make(name, lambda p, t=prompt, s=seconds: eleven.sound_effect(t, p, s))
    for name, (voice, text) in VOICES.items():
        make(name, lambda p, v=voice, t=text: eleven.speech(t, v, p))
    return 0


if __name__ == "__main__":
    sys.exit(main())
