---
name: elevenlabs-voice
description: Transcribes audio via ElevenLabs Scribe (with optional speaker diarization) and generates speech via ElevenLabs text-to-speech. Use for any speech-to-text or text-to-speech need, e.g. "transcribe this recording", "what does this voice note say", "read this aloud", "make a TTS of this". Handles mixed-language audio. Delivery-agnostic.
---

# ElevenLabs Voice — Speech ↔ Text Helpers

Two thin shell helpers that ship inside this skill and wrap the ElevenLabs HTTP API:

- `"${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/transcribe.sh"` — audio file → text
- `"${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/tts.sh"` — text → audio file

They do not capture mic input, play audio, or send anything to a chat app. Delivery is the caller's job.

## Prerequisites

Requires `curl`, `jq`, `python3` and an ElevenLabs API key. If the helpers fail with "API key not found", point the user to `SETUP.md` at the plugin root (section: **elevenlabs-voice**) and stop until it's configured.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/elevenlabs-voice.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/elevenlabs-voice.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/elevenlabs-voice.md` — edit anytime to customize."
2. Read it. Export each populated field as its env var on the helper call (e.g. `ELEVENLABS_VOICE_ID=<voice_id> bash .../tts.sh "..."`). Empty fields fall back to the defaults in the table below.

| Preference | Env var | Default |
|------------|---------|---------|
| `voice_id` | `ELEVENLABS_VOICE_ID` | `JBFqnCBsd6RMkjVDRZzb` (ElevenLabs' premade "George") |
| `tts_model` | `ELEVENLABS_MODEL` | `eleven_v3` (broadest language coverage) |
| `output_format` | `ELEVENLABS_FORMAT` | `opus_48000_64` (`mp3_44100_128` for `.mp3`, `pcm_16000` for raw PCM) |
| `speed` | `ELEVENLABS_SPEED` | `1.0` (0.7–1.2, no pitch shift) |
| `stability` | `ELEVENLABS_STABILITY` | `0.5` (lower = more expressive/variable) |
| `stt_model` | `ELEVENLABS_STT_MODEL` | `scribe_v2` (handles code-switching) |
| `api_key_file` | `ELEVENLABS_API_KEY_FILE` | `~/.config/elevenlabs/api_key` |

The key is read from `$ELEVENLABS_API_KEY` if set, else from the key file. Never print it.

## Transcribe: `transcribe.sh [--diarize] <audio-file>` → transcript on stdout

Posts to `https://api.elevenlabs.io/v1/speech-to-text`. Auto-detects language and handles several languages in one clip.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/transcribe.sh" /path/to/audio.ogg
```

**Speaker diarization:** pass `--diarize` (or set `ELEVENLABS_DIARIZE=1`) for multi-speaker audio (meetings, interviews). It emits grouped, timestamped turns (`[mm:ss] speaker_0: ...`). Without it you get one flat block and inferring who said what is unreliable, so always diarize meetings. Speaker ids are anonymous; map them to names from the content afterwards.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/transcribe.sh" --diarize ~/Downloads/meeting.m4a
```

**Timeout** is dynamic: 10s per MB, minimum 120s. Override with `ELEVENLABS_MAX_TIME=<seconds>`, but never lower than the file size warrants.

**Cutting a clip by what is said:** use `cut-clip` rather than hand-rolling a word-timestamp lookup.

## Speak: `tts.sh "<text>" [output-path]` → output path on stdout

Posts to `https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream`. Default output is `/tmp/tts_<timestamp>.ogg`.

```bash
bash "${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/tts.sh" "Hello there." ~/Downloads/hello.ogg

# Text from stdin:
echo "Long text..." | bash "${CLAUDE_PLUGIN_ROOT}/skills/elevenlabs-voice/tts.sh" - /tmp/reply.ogg
```

Print the output path; the caller plays or attaches it.

## Voice-reply guidance

When producing a spoken reply for a chat or voice interface:
- Keep each clip under ~1500 characters; longer monologues feel wrong as voice and burn quota. Fall back to text and say why.
- Fall back to text when the reply is mostly code, lists or tables.
- If transcription plus processing will take more than a couple of seconds, send a short text acknowledgment first.

## Cost

Both endpoints are metered (STT per audio minute, TTS per character). Check current pricing and usage at elevenlabs.io before running large batches.

## Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| Transcript drops one language | `scribe_v1` detects one language at a time | Use the default `scribe_v2` |
| `voice_not_found` | Voice id isn't in this account's library | List ids: `curl -s -H "xi-api-key: $ELEVENLABS_API_KEY" https://api.elevenlabs.io/v1/voices \| jq '.voices[] \| {voice_id, name}'` |
| A language sounds accented or wrong | The model doesn't list that language | Use `eleven_v3` and a voice native to that language |
| Empty/garbled transcript | Truncated audio, non-voice content, or quota exceeded | Check the audio plays; check quota in the ElevenLabs dashboard |
| `API key not found` | Key file missing and env var unset | See SETUP.md |
