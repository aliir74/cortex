---
name: cut-clip
description: Use when cutting, trimming or extracting a segment from a video or audio file, especially when the boundaries are given as spoken phrases rather than timecodes. Triggers on "cut this clip", "trim the video", "clip from X to Y", "cut from the moment it says", and on a video URL plus a quoted phrase.
---

# Cut Clip

Cuts a segment out of a video or audio file where the user marks the boundaries by
what is **said** rather than by timecode. One script handles the download, the
transcription, the phrase lookup, the cut and the verification.

## Prerequisites

Requires `yt-dlp`, `ffmpeg` (with `ffprobe`), `curl`, Python 3, and an ElevenLabs API
key (transcription is ElevenLabs Scribe; the `elevenlabs-voice` skill uses the same
key). If anything is missing, point the user to `SETUP.md` at the plugin root
(section: **cut-clip**) and stop until it's available.

## The command

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/cut-clip/cut_clip.py" <url-or-path> \
  --from "<opening phrase>" --to "<closing phrase>" [--out PATH]
```

`<url-or-path>` is any URL yt-dlp handles (YouTube, Instagram, TikTok, X, ...) or a
local media path. Default output is `./<stem>-clip.mp4` in the current directory.

The script prints the resolved start and end with the matched words, the output path
and duration, and a re-transcription of the finished cut. Read that `verify` line: it
is the evidence the clip actually starts and ends where the user asked.

## Flags worth knowing

| Flag | Use |
|---|---|
| `--list` | Dump every word with its timestamp and cut nothing. The fallback when a phrase will not match, and the way to answer "where in the video does X happen". |
| `--to "phrase..."` | A trailing `...` keeps the run-on words after the phrase, up to the next pause. Use it whenever the user writes the closing phrase with an ellipsis. |
| `--from-occurrence N` / `--to-occurrence N` | Pick a later repeat. The script reports how many places each phrase matched. |
| `--pad-start` / `--pad-end` | Seconds of breathing room, default 0.15 / 0.10. |
| `--copy` | Stream-copy instead of re-encoding. Faster, but the cut snaps to keyframes, so the start drifts. Only when the user asks for speed. |
| `--language <code>` | ISO language hint (e.g. `eng`, `fas`) when auto-detection picks wrong. |
| `--no-verify` | Skip the verification pass (saves a second API call). |

## Behaviour that matters

- **The transcript is cached**: next to a local source as `<file>.stt.json`, or under
  `~/.cache/cut-clip/` for URLs. A second cut from the same source costs no API call.
  Delete the cache file to force a re-transcription.
- **Phrase matching is spelling-tolerant.** Punctuation, case, and Persian/Arabic
  spelling variants (ZWNJ, Arabic ي/ك, diacritics, Arabic-Indic digits) are folded
  before matching, so a typed phrase matches ASR output that spells it differently.
- **A fuzzy match is reported as `[fuzzy 0.86]`.** ASR sometimes mishears a word, and
  the same audio can transcribe differently between runs. When the ratio is below
  about 0.8, check the matched words in the output line before handing the clip over.
- **When a phrase will not match at all**, the script prints the five closest windows
  with their timestamps and exits. Re-run with `--list`, find the moment, and cut by
  hand with ffmpeg rather than guessing at a different phrasing.

## When the user gives timecodes instead of phrases

Skip the script: `ffmpeg -y -ss <start> -to <end> -i <in> -c:v libx264 -crf 18 -c:a aac -b:a 192k -movflags +faststart <out>`.

## Reporting the result

Report the output path, the duration, the source timespan, and the `verify` line.
