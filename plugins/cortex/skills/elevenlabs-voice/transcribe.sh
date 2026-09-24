#!/bin/bash
# transcribe.sh — transcribe an audio file via ElevenLabs Scribe v2
#
# Usage:
#   transcribe.sh <audio-file>
#   transcribe.sh --diarize <audio-file>     # speaker-labeled turns
#
# Outputs the transcript to stdout. Auto-detects language, including mixed-language audio.
# Returns non-zero on error and writes the error JSON to stderr.
#
# Diarization: pass --diarize (or set ELEVENLABS_DIARIZE=1) to request
# per-word speaker_id and emit grouped, timestamped speaker turns like
# "[mm:ss] speaker_0: ...". Use this for meetings / multi-speaker audio;
# without it, inferring who said what from a flat block is unreliable.

set -euo pipefail

DIARIZE="${ELEVENLABS_DIARIZE:-}"
if [ "${1:-}" = "--diarize" ]; then
  DIARIZE=1
  shift
fi

FILE="${1:-}"
if [ -z "$FILE" ] || [ ! -f "$FILE" ]; then
  echo "ERROR: audio file not found: ${FILE:-<missing>}" >&2
  echo "Usage: $0 [--diarize] <audio-file>" >&2
  exit 1
fi

if [ -n "${ELEVENLABS_API_KEY:-}" ]; then
  API_KEY="$ELEVENLABS_API_KEY"
else
  KEY_FILE="${ELEVENLABS_API_KEY_FILE:-$HOME/.config/elevenlabs/api_key}"
  if [ ! -r "$KEY_FILE" ]; then
    echo "ERROR: ElevenLabs API key not found (set ELEVENLABS_API_KEY or create $KEY_FILE)" >&2
    exit 1
  fi
  API_KEY="$(tr -d '[:space:]' < "$KEY_FILE")"
fi

MODEL="${ELEVENLABS_STT_MODEL:-scribe_v2}"

# Dynamic timeout: 10s per MB, minimum 120s. Override with ELEVENLABS_MAX_TIME.
FILE_MB=$(( ($(wc -c < "$FILE") + 1048575) / 1048576 ))
DEFAULT_MAX_TIME=$(( FILE_MB * 10 < 120 ? 120 : FILE_MB * 10 ))
MAX_TIME="${ELEVENLABS_MAX_TIME:-$DEFAULT_MAX_TIME}"

DIARIZE_ARG=()
if [ -n "$DIARIZE" ]; then
  DIARIZE_ARG=(-F "diarize=true")
fi

RESP="$(curl -sS -X POST https://api.elevenlabs.io/v1/speech-to-text \
  -H "xi-api-key: $API_KEY" \
  -F "model_id=$MODEL" \
  ${DIARIZE_ARG[@]+"${DIARIZE_ARG[@]}"} \
  -F "file=@$FILE" \
  --max-time "$MAX_TIME")"

TEXT="$(echo "$RESP" | jq -r '.text // empty')"
if [ -z "$TEXT" ]; then
  echo "ERROR: transcription failed" >&2
  echo "$RESP" >&2
  exit 2
fi

if [ -z "$DIARIZE" ]; then
  printf '%s\n' "$TEXT"
  exit 0
fi

# Diarized: group consecutive words by speaker_id into timestamped turns.
echo "$RESP" | python3 -c '
import json, sys
d = json.load(sys.stdin)
words = d.get("words", [])
if not words:
    print(d.get("text", ""))
    sys.exit(0)
def fmt(s):
    return "??:??" if s is None else f"{int(s//60):02d}:{int(s%60):02d}"
turns, cur = [], None
for w in words:
    if w.get("type") == "spacing":
        if cur: cur["text"] += w.get("text", "")
        continue
    spk = w.get("speaker_id")
    if cur is None or spk != cur["spk"]:
        if cur: turns.append(cur)
        cur = {"spk": spk, "start": w.get("start"), "text": w.get("text", "")}
    else:
        cur["text"] += w.get("text", "")
if cur: turns.append(cur)
print("\n\n".join("[%s] %s: %s" % (fmt(t["start"]), t["spk"], t["text"].strip()) for t in turns))
'
