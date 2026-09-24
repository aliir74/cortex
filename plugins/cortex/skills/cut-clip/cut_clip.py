#!/usr/bin/env python3
"""cut_clip.py - cut a video/audio segment identified by spoken phrases.

Pipeline: fetch (yt-dlp for URLs) -> extract audio -> ElevenLabs Scribe word
timestamps (cached) -> locate the phrases -> ffmpeg cut -> re-transcribe to verify.

Stdlib only. Shells out to yt-dlp, ffmpeg, ffprobe, curl.

Usage:
  cut_clip.py <url-or-path> --from "<phrase>" --to "<phrase>" [--out PATH]
  cut_clip.py <url-or-path> --list            # dump timestamped transcript, cut nothing
"""

import argparse
import difflib
import json
import os
import re
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unicodedata

API_URL = "https://api.elevenlabs.io/v1/speech-to-text"
# Key lookup order: $ELEVENLABS_API_KEY, then the file at
# $ELEVENLABS_API_KEY_FILE (default ~/.config/elevenlabs/api_key).
KEY_FILE = os.path.expanduser(
    os.environ.get("ELEVENLABS_API_KEY_FILE", "~/.config/elevenlabs/api_key")
)
MODEL = os.environ.get("ELEVENLABS_STT_MODEL", "scribe_v2")
# Trailing-off markers: when --to ends with one, keep the words that run on
# after the match until the next real pause.
TRAIL_MARKERS = ("...", "…")
TRAIL_GAP = 0.35  # seconds of silence that ends a trailing run-on


def die(msg, code=1):
    print("ERROR: %s" % msg, file=sys.stderr)
    sys.exit(code)


def run(cmd, **kw):
    kw.setdefault("stdout", subprocess.PIPE)
    kw.setdefault("stderr", subprocess.PIPE)
    p = subprocess.run(cmd, text=True, **kw)
    if p.returncode != 0:
        die("%s failed (exit %d)\n%s" % (cmd[0], p.returncode, (p.stderr or "")[-2000:]))
    return p.stdout


def need(binary):
    if not shutil.which(binary):
        die("%s not found on PATH" % binary)


# ---------------------------------------------------------------- normalizing

ZWNJ = "‌"
TATWEEL = "ـ"
DIACRITICS = re.compile("[ً-ْٰٓ-ٕ]")
ARABIC_TO_PERSIAN = {"ي": "ی", "ى": "ی", "ك": "ک"}
DIGITS = {ord(c): str(i % 10) for i, c in enumerate("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩")}
PUNCT = re.compile(r"[^\w\s]", re.UNICODE)


def normalize(text):
    """Fold Persian/Arabic spelling variants so ASR output matches a typed phrase."""
    text = unicodedata.normalize("NFC", text)
    for a, p in ARABIC_TO_PERSIAN.items():
        text = text.replace(a, p)
    text = text.replace(ZWNJ, "").replace(TATWEEL, "")
    text = DIACRITICS.sub("", text)
    text = text.translate(DIGITS)
    text = PUNCT.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip().lower()


# ------------------------------------------------------------------- fetching


def fetch_source(source, workdir):
    if re.match(r"^https?://", source):
        need("yt-dlp")
        out = os.path.join(workdir, "source.%(ext)s")
        run(["yt-dlp", "--no-progress", "-o", out, source])
        found = [
            os.path.join(workdir, f)
            for f in os.listdir(workdir)
            if f.startswith("source.")
        ]
        if not found:
            die("yt-dlp produced no file")
        return max(found, key=os.path.getsize)
    path = os.path.expanduser(source)
    if not os.path.isfile(path):
        die("source not found: %s" % path)
    return path


def extract_audio(media, workdir):
    need("ffmpeg")
    audio = os.path.join(workdir, "audio.mp3")
    run(["ffmpeg", "-y", "-i", media, "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "libmp3lame", "-b:a", "48k", audio])
    return audio


# --------------------------------------------------------------- transcribing


def transcribe(audio, cache=None, language=None):
    if cache and os.path.isfile(cache):
        with open(cache) as fh:
            return json.load(fh)
    need("curl")
    key = os.environ.get("ELEVENLABS_API_KEY", "").strip()
    if not key:
        if not os.path.isfile(KEY_FILE):
            die("ElevenLabs API key not found: set ELEVENLABS_API_KEY or create %s"
                % KEY_FILE)
        with open(KEY_FILE) as fh:
            key = fh.read().strip()
    cmd = ["curl", "-sS", "-X", "POST", API_URL,
           "-H", "xi-api-key: %s" % key,
           "-F", "model_id=%s" % MODEL,
           "-F", "file=@%s" % audio,
           "--max-time", "600"]
    if language:
        cmd += ["-F", "language_code=%s" % language]
    raw = run(cmd)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        die("transcription returned non-JSON:\n%s" % raw[:1000])
    if "words" not in data and "text" not in data:
        die("transcription failed:\n%s" % raw[:1000])
    if cache:
        with open(cache, "w") as fh:
            json.dump(data, fh, ensure_ascii=False)
    return data


def cache_path(source, media):
    """Stable transcript cache, keyed by the source the user gave.

    A URL's download lands in a temp dir that is deleted on exit, so caching
    beside the media would throw the transcript away every run.
    """
    if re.match(r"^https?://", source):
        d = os.path.expanduser("~/.cache/cut-clip")
        os.makedirs(d, exist_ok=True)
        key = hashlib.sha256(source.encode()).hexdigest()[:16]
        return os.path.join(d, key + ".stt.json")
    return os.path.abspath(media) + ".stt.json"


def real_words(data):
    """Spoken words only, with timings. Drops spacing tokens and [sound] events."""
    out = []
    for w in data.get("words", []):
        if w.get("type") == "spacing":
            continue
        text = (w.get("text") or "").strip()
        if not text or (text.startswith("[") and text.endswith("]")):
            continue
        if w.get("start") is None:
            continue
        out.append({
            "text": text,
            "norm": normalize(text),
            "start": float(w["start"]),
            "end": float(w.get("end", w["start"])),
        })
    return out


# ----------------------------------------------------------------- locating


def find_phrase(words, phrase, occurrence=1):
    """Return ((i, j, ratio, n_hits), None) for the occurrence-th match.

    Matching runs over the normalized words joined into one string, so a hit is
    anchored to real word boundaries: a phrase never silently absorbs the words
    in front of it. Falls back to the best fuzzy window, which matters because
    ASR sometimes mishears a word or two.
    """
    target = normalize(phrase.rstrip("".join(TRAIL_MARKERS) + " "))
    if not target:
        die("--from/--to phrase is empty after normalizing")
    n_target = len(target.split())

    joined = ""
    starts = []   # char offset where each word begins
    ends = []     # char offset just past each word
    for w in words:
        if joined:
            joined += " "
        starts.append(len(joined))
        joined += w["norm"]
        ends.append(len(joined))

    hits = []
    pos = joined.find(target)
    while pos != -1:
        if pos in starts:
            i = starts.index(pos)
            stop = pos + len(target)
            j = i + 1
            while j < len(words) and ends[j - 1] < stop:
                j += 1
            hits.append((i, j, 1.0))
        pos = joined.find(target, pos + 1)

    if not hits:
        scored = []
        for i in range(len(words)):
            for span in range(max(1, n_target - 1), n_target + 2):
                j = min(len(words), i + span)
                window = " ".join(w["norm"] for w in words[i:j])
                scored.append(
                    (difflib.SequenceMatcher(None, target, window).ratio(), i, j))
        scored.sort(key=lambda t: (-t[0], t[1]))
        deduped, seen = [], set()
        for r, i, j in scored:
            if i in seen:
                continue
            seen.add(i)
            deduped.append((r, i, j))
        best = [(i, j, r) for r, i, j in deduped[:5] if r >= 0.6]
        if not best:
            return None, deduped[:5]
        hits = best

    if occurrence > len(hits):
        die("phrase %r found %d time(s), --occurrence %d requested"
            % (phrase, len(hits), occurrence))
    i, j, ratio = hits[occurrence - 1]
    return (i, j, ratio, len(hits)), None


def extend_trailing(words, j):
    """Absorb run-on words after the match until a real pause."""
    while j < len(words) and words[j]["start"] - words[j - 1]["end"] < TRAIL_GAP:
        j += 1
    return j


# -------------------------------------------------------------------- cutting


def cut(media, start, end, out, reencode=True):
    need("ffmpeg")
    cmd = ["ffmpeg", "-y", "-ss", "%.3f" % start, "-to", "%.3f" % end, "-i", media]
    if reencode:
        cmd += ["-c:v", "libx264", "-crf", "18", "-preset", "medium",
                "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-c", "copy"]
    cmd += ["-movflags", "+faststart", out]
    run(cmd)
    return out


def duration(path):
    need("ffprobe")
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                      "-of", "csv=p=0", path]).strip())


def fmt(t):
    return "%d:%05.2f" % (int(t // 60), t % 60)


# ----------------------------------------------------------------------- main


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source", help="URL (yt-dlp) or local media path")
    ap.add_argument("--from", dest="start_phrase", help="phrase the clip starts on")
    ap.add_argument("--to", dest="end_phrase",
                    help="phrase the clip ends on; end it with ... to keep the run-on")
    ap.add_argument("--out", help="output path (default ./<stem>-clip.mp4)")
    ap.add_argument("--list", action="store_true",
                    help="print the timestamped transcript and exit")
    ap.add_argument("--from-occurrence", type=int, default=1)
    ap.add_argument("--to-occurrence", type=int, default=1)
    ap.add_argument("--pad-start", type=float, default=0.15)
    ap.add_argument("--pad-end", type=float, default=0.10)
    ap.add_argument("--language", help="ISO code hint, e.g. fas, eng")
    ap.add_argument("--copy", action="store_true",
                    help="stream-copy instead of re-encoding (keyframe-snapped, faster)")
    ap.add_argument("--no-verify", action="store_true")
    ap.add_argument("--keep-temp", action="store_true")
    args = ap.parse_args()

    if not args.list and not (args.start_phrase and args.end_phrase):
        ap.error("--from and --to are required unless --list is given")

    workdir = tempfile.mkdtemp(prefix="cut-clip-")
    try:
        media = fetch_source(args.source, workdir)
        audio = extract_audio(media, workdir)
        cache = cache_path(args.source, media)
        data = transcribe(audio, cache=cache, language=args.language)
        words = real_words(data)
        if not words:
            die("transcript has no timed words")

        if args.list:
            for k, w in enumerate(words):
                print("%4d  %s  %s" % (k, fmt(w["start"]), w["text"]))
            print("\n%d words, media %.2fs, transcript cached at %s"
                  % (len(words), duration(media), cache), file=sys.stderr)
            return

        hit_a, near_a = find_phrase(words, args.start_phrase, args.from_occurrence)
        if hit_a is None:
            print("Could not locate --from %r. Closest windows:" % args.start_phrase,
                  file=sys.stderr)
            for r, i, j in near_a:
                print("  %.2f  %s  %s" % (r, fmt(words[i]["start"]),
                                          " ".join(w["text"] for w in words[i:j])),
                      file=sys.stderr)
            die("no match for --from; re-run with --list and pick timestamps by hand")
        i_a, j_a, ratio_a, n_a = hit_a

        hit_b, near_b = find_phrase(words[j_a - 1:], args.end_phrase, args.to_occurrence)
        if hit_b is None:
            print("Could not locate --to %r after the start. Closest windows:"
                  % args.end_phrase, file=sys.stderr)
            for r, i, j in near_b:
                k = i + j_a - 1
                print("  %.2f  %s  %s" % (r, fmt(words[k]["start"]),
                                          " ".join(w["text"] for w in
                                                   words[k:k + (j - i)])),
                      file=sys.stderr)
            die("no match for --to; re-run with --list and pick timestamps by hand")
        i_b, j_b, ratio_b, n_b = hit_b
        i_b += j_a - 1
        j_b += j_a - 1

        if args.end_phrase.rstrip().endswith(TRAIL_MARKERS):
            j_b = extend_trailing(words, j_b)

        start = max(0.0, words[i_a]["start"] - args.pad_start)
        end = min(duration(media), words[j_b - 1]["end"] + args.pad_end)
        if end <= start:
            die("computed end (%.2f) is not after start (%.2f)" % (end, start))

        out = args.out or os.path.abspath(
            "%s-clip.mp4" % os.path.splitext(os.path.basename(media))[0])
        out = os.path.expanduser(out)
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        cut(media, start, end, out, reencode=not args.copy)

        print("start  %s  (%s)%s" % (fmt(start),
                                     " ".join(w["text"] for w in words[i_a:j_a]),
                                     "" if ratio_a == 1.0 else
                                     "  [fuzzy %.2f]" % ratio_a))
        print("end    %s  (%s)%s" % (fmt(end),
                                     " ".join(w["text"] for w in words[i_b:j_b]),
                                     "" if ratio_b == 1.0 else
                                     "  [fuzzy %.2f]" % ratio_b))
        if n_a > 1 or n_b > 1:
            print("note   --from matched %d place(s), --to %d; use "
                  "--from-occurrence/--to-occurrence to pick another" % (n_a, n_b))
        print("out    %s  (%.2fs)" % (out, duration(out)))

        if not args.no_verify:
            vaudio = extract_audio(out, workdir)
            vdata = transcribe(vaudio)
            print("verify %s" % (vdata.get("text", "").strip() or "<no speech>"))
    finally:
        if args.keep_temp:
            print("temp   %s" % workdir, file=sys.stderr)
        else:
            shutil.rmtree(workdir, ignore_errors=True)


if __name__ == "__main__":
    main()
