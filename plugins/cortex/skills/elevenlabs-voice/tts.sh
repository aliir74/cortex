#!/bin/bash
# tts.sh — generate a voice clip via the ElevenLabs text-to-speech API
#
# Usage:
#   tts.sh "text to speak" [output-path]
#
# Default output: /tmp/tts_<timestamp>.ogg (Opus 48kHz).
# Prints the absolute output path to stdout on success.
# Reads text from stdin if first arg is "-".
#
# Auth: $ELEVENLABS_API_KEY, else the file at $ELEVENLABS_API_KEY_FILE
# (default ~/.config/elevenlabs/api_key, chmod 600).
#
# Env overrides:
#   ELEVENLABS_VOICE_ID  voice (default: JBFqnCBsd6RMkjVDRZzb, ElevenLabs' premade "George")
#   ELEVENLABS_MODEL     model (default: eleven_v3; broadest language coverage)
#   ELEVENLABS_FORMAT    output format (default: opus_48000_64; use mp3_44100_128 for .mp3)
#   ELEVENLABS_SPEED     tempo 0.7–1.2 (default: 1.0)
#   ELEVENLABS_STABILITY 0.0–1.0 (default: 0.5; lower = more emotional/variable)

set -euo pipefail

if [ "${1:-}" = "-" ]; then
  TEXT="$(cat)"
  OUT="${2:-/tmp/tts_$(date +%s).ogg}"
else
  TEXT="${1:-}"
  OUT="${2:-/tmp/tts_$(date +%s).ogg}"
fi

if [ -z "$TEXT" ]; then
  echo "ERROR: missing text" >&2
  echo "Usage: $0 \"text\" [output-path]   |   echo text | $0 - [output-path]" >&2
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

VOICE="${ELEVENLABS_VOICE_ID:-JBFqnCBsd6RMkjVDRZzb}"
MODEL="${ELEVENLABS_MODEL:-eleven_v3}"
FORMAT="${ELEVENLABS_FORMAT:-opus_48000_64}"
SPEED="${ELEVENLABS_SPEED:-1.0}"
STABILITY="${ELEVENLABS_STABILITY:-0.5}"

mkdir -p "$(dirname "$OUT")"

curl -sS -X POST "https://api.elevenlabs.io/v1/text-to-speech/${VOICE}/stream?output_format=${FORMAT}" \
  -H "xi-api-key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d "$(jq -n --arg t "$TEXT" --arg m "$MODEL" --argjson s "$SPEED" --argjson st "$STABILITY" \
    '{text:$t, model_id:$m, voice_settings:{stability:$st, speed:$s}}')" \
  -o "$OUT" \
  --max-time 120 \
  --fail-with-body || {
    echo "ERROR: TTS request failed" >&2
    if [ -f "$OUT" ]; then cat "$OUT" >&2; rm -f "$OUT"; fi
    exit 2
  }

# Sanity check: should be audio, not JSON error
if file "$OUT" | grep -qi "JSON\|ASCII text"; then
  echo "ERROR: API returned non-audio response:" >&2
  cat "$OUT" >&2
  rm -f "$OUT"
  exit 2
fi

printf '%s\n' "$OUT"
