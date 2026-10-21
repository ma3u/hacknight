#!/usr/bin/env bash
# Generate the Vinland pub quiz soundscape with the ElevenLabs CLI into frontend/sounds/.
#
#   brew install elevenlabs/tap/elevenlabs      # or: npm install -g @elevenlabs/cli
#   elevenlabs auth login                       # or export ELEVENLABS_API_KEY (e.g. from your TwoBreath .env)
#   ./frontend/make_sounds.sh                   # add --force to regenerate existing files
#
# Each file costs ElevenLabs credits once; existing files are skipped. The frontend plays
# whatever is there and stays silent for missing files.
set -euo pipefail

OUT="$(cd "$(dirname "$0")" && pwd)/sounds"
FORCE="${1:-}"
mkdir -p "$OUT"

command -v elevenlabs >/dev/null || { echo "❌ elevenlabs CLI not found: brew install elevenlabs/tap/elevenlabs"; exit 1; }

sfx() {  # sfx <file> <prompt>
  local file="$OUT/$1"
  if [[ -f "$file" && "$FORCE" != "--force" ]]; then echo "⏭  $1 exists"; return; fi
  echo "🎵 $1"
  elevenlabs text-to-sound-effects convert --text "$2" --output "$file"
}

# Background music: a real track if this CLI version has a music command, else an ambient SFX loop.
MUSIC_PROMPT="Epic Nordic Viking folk background music for a pub quiz: frame drums and taiko, deep throat-singing drones, tagelharpa and hurdy-gurdy, steady mid tempo, adventurous but calm enough to think, instrumental, no lyrics, seamless loop"
if [[ ! -f "$OUT/music.mp3" || "$FORCE" == "--force" ]]; then
  if elevenlabs music --help >/dev/null 2>&1; then
    echo "🎵 music.mp3 (music API)"
    elevenlabs music compose --prompt "$MUSIC_PROMPT" --music-length-ms 120000 --output "$OUT/music.mp3" \
      || sfx music.mp3 "Seamless loop of Nordic Viking ambient music, frame drums, low throat-singing drone, tagelharpa, calm and adventurous"
  else
    sfx music.mp3 "Seamless loop of Nordic Viking ambient music, frame drums, low throat-singing drone, tagelharpa, calm and adventurous"
  fi
fi

sfx horn.mp3    "Deep Viking war horn blast echoing across a misty fjord, single long call"
sfx drum.mp3    "Short Viking war drum hit followed by a wooden shield bash, punchy"
sfx reveal.mp3  "Steel sword drawn from its scabbard with a bright metallic ring"
sfx cheer.mp3   "Viking village crowd cheering and roaring Skål, wooden mugs clinking, triumphant, short"
sfx groan.mp3   "Disappointed Viking tavern crowd groaning ohhh, a few laughs, short"
sfx victory.mp3 "Huge Viking village victory celebration: crowd chanting and stomping, war horns and drums, mead hall feast"

echo "✅ Sounds in $OUT"
ls -lh "$OUT"
