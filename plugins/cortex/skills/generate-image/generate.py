#!/usr/bin/env python3
"""
Generate or edit an image via Google Gemini (Nano Banana) or OpenAI (GPT Image).

Stdlib-only. Reads $GEMINI_API_KEY or $OPENAI_API_KEY from env (per provider).

Usage:
  generate.py --prompt "<photographer brief>" --output path/to/file.png
  generate.py --prompt "..." --output ... --quality medium
  generate.py --provider gemini --prompt "..." --output ... --aspect-ratio 4:3
  generate.py --provider openai --model gpt-image-2 --size 1536x1024 ...

Edit mode (image-in, image-out) — pass one or more --input-image paths:
  generate.py --prompt "add a hat" --input-image cat.png --output cat-hat.png
  generate.py --prompt "blend these" --input-image a.png --input-image b.png --output merge.png
  generate.py --provider openai --prompt "fill in" --input-image base.png --mask mask.png --output out.png

Output (prefixed lines for the calling skill to parse):
  STATUS: ok | error
  PATH: /abs/path/to/saved.png        (on success)
  BYTES: 123456                       (on success)
  PROVIDER: gemini|openai             (on success)
  MODEL: <model-name>                 (on success)
  MODE: generate|edit                 (on success)
  USAGE: <json>                       (on success, OpenAI only — token counts)
  ERROR: <message>                    (on failure)
"""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

GEMINI_DEFAULT_MODEL = "gemini-2.5-flash-image"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com/v1beta/models"

OPENAI_DEFAULT_MODEL = "gpt-image-1.5"  # No org verification required; comparable quality
OPENAI_API_URL = "https://api.openai.com/v1/images/generations"
OPENAI_EDIT_URL = "https://api.openai.com/v1/images/edits"


def emit(key: str, value) -> None:
    print(f"{key}: {value}", flush=True)


def post_json(url: str, body: dict, headers: dict, timeout: int = 180) -> dict:
    """POST JSON; return decoded JSON or raise with (status_code, body_text)."""
    req = urllib.request.Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    return _do_request(req, timeout)


def post_multipart(url: str, fields: dict, files: list, headers: dict, timeout: int = 180) -> dict:
    """POST multipart/form-data. `files` is a list of (field_name, filename, content_bytes, mime)."""
    boundary = "----ClaudeBoundary" + os.urandom(12).hex()
    parts: list[bytes] = []
    for k, v in fields.items():
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(f'Content-Disposition: form-data; name="{k}"\r\n\r\n'.encode())
        parts.append(f"{v}\r\n".encode())
    for name, filename, content, mime in files:
        parts.append(f"--{boundary}\r\n".encode())
        parts.append(
            f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'.encode()
        )
        parts.append(f"Content-Type: {mime}\r\n\r\n".encode())
        parts.append(content)
        parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)

    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
            **headers,
        },
        method="POST",
    )
    return _do_request(req, timeout)


def _do_request(req: urllib.request.Request, timeout: int) -> dict:
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(body_text).get("error", {})
            msg = err.get("message", body_text)
        except Exception:
            msg = body_text
        raise RuntimeError(f"HTTP {e.code}: {msg[:500]}")


def _load_image(path: str) -> tuple[str, bytes, str]:
    """Resolve path, read bytes, guess mime. Returns (filename, content, mime)."""
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise RuntimeError(f"Input image not found: {p}")
    mime, _ = mimetypes.guess_type(str(p))
    return p.name, p.read_bytes(), (mime or "image/png")


def generate_gemini(
    prompt: str,
    model: str,
    aspect_ratio: str | None,
    image_paths: list[str] | None = None,
) -> tuple[bytes, str]:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set in environment")

    full_prompt = prompt
    if aspect_ratio:
        full_prompt = f"{prompt}\n\nAspect ratio: {aspect_ratio}."

    parts: list[dict] = [{"text": full_prompt}]
    for path in image_paths or []:
        _, content, mime = _load_image(path)
        parts.append({
            "inline_data": {
                "mime_type": mime,
                "data": base64.b64encode(content).decode("ascii"),
            }
        })

    url = f"{GEMINI_API_BASE}/{model}:generateContent?key={api_key}"
    data = post_json(url, {"contents": [{"parts": parts}]}, headers={})

    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates: {json.dumps(data)[:300]}")

    for part in candidates[0].get("content", {}).get("parts", []):
        inline = part.get("inlineData") or part.get("inline_data")
        if inline and inline.get("data"):
            return base64.b64decode(inline["data"]), (inline.get("mimeType") or "image/png")

    text_parts = [p.get("text", "") for p in candidates[0].get("content", {}).get("parts", []) if p.get("text")]
    raise RuntimeError(f"No image in response. Model text: {' '.join(text_parts)[:300]}")


def generate_openai(prompt: str, model: str, size: str, quality: str) -> tuple[bytes, str, dict]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    body = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": 1,
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    data = post_json(OPENAI_API_URL, body, headers=headers)

    items = data.get("data", [])
    if not items or "b64_json" not in items[0]:
        raise RuntimeError(f"No b64_json in response: {json.dumps(data)[:300]}")

    return base64.b64decode(items[0]["b64_json"]), "image/png", data.get("usage", {})


def edit_openai(
    prompt: str,
    model: str,
    size: str,
    quality: str,
    image_paths: list[str],
    mask_path: str | None,
) -> tuple[bytes, str, dict]:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set in environment")

    fields = {
        "model": model,
        "prompt": prompt,
        "size": size,
        "quality": quality,
        "n": "1",
    }

    files: list = []
    field_name = "image[]" if len(image_paths) > 1 else "image"
    for path in image_paths:
        filename, content, mime = _load_image(path)
        files.append((field_name, filename, content, mime))
    if mask_path:
        filename, content, mime = _load_image(mask_path)
        files.append(("mask", filename, content, mime))

    headers = {"Authorization": f"Bearer {api_key}"}
    data = post_multipart(OPENAI_EDIT_URL, fields, files, headers=headers)

    items = data.get("data", [])
    if not items or "b64_json" not in items[0]:
        raise RuntimeError(f"No b64_json in response: {json.dumps(data)[:300]}")

    return base64.b64decode(items[0]["b64_json"]), "image/png", data.get("usage", {})


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--prompt", required=True, help="Full photographer-brief prompt")
    p.add_argument("--output", required=True, help="Destination PNG path (absolute or relative)")
    p.add_argument("--provider", choices=["gemini", "openai"], default="openai",
                   help="Which API to call (default: openai)")
    p.add_argument("--model", default=None,
                   help="Override model. Gemini default: gemini-2.5-flash-image. OpenAI default: gpt-image-1.5.")
    # Gemini-only
    p.add_argument("--aspect-ratio", default=None,
                   help="(gemini) Aspect ratio hint baked into prompt, e.g. 1:1, 4:3, 3:4.")
    # OpenAI-only
    p.add_argument("--size", default="1024x1024",
                   help="(openai) Size, e.g. 1024x1024, 1536x1024, 1024x1536. Default: 1024x1024.")
    p.add_argument("--quality", default="medium", choices=["low", "medium", "high", "auto"],
                   help="(openai) Quality tier. Default: medium.")
    # Edit-mode (image-in, image-out)
    p.add_argument("--input-image", action="append", default=None,
                   help="Source image path for edit mode. Repeat for multi-image edits "
                        "(blend / compose). When set, routes to provider edit endpoint.")
    p.add_argument("--mask", default=None,
                   help="(openai edit) Optional mask PNG — transparent pixels mark the area to edit.")
    args = p.parse_args()

    edit_mode = bool(args.input_image)
    if args.mask and not edit_mode:
        emit("STATUS", "error")
        emit("ERROR", "--mask requires --input-image")
        return 1

    try:
        if args.provider == "gemini":
            model = args.model or GEMINI_DEFAULT_MODEL
            if args.mask:
                raise RuntimeError("--mask is OpenAI-only; Gemini doesn't accept an inpaint mask.")
            img_bytes, mime = generate_gemini(args.prompt, model, args.aspect_ratio, args.input_image)
            usage = None
        else:
            model = args.model or OPENAI_DEFAULT_MODEL
            if edit_mode:
                img_bytes, mime, usage = edit_openai(
                    args.prompt, model, args.size, args.quality, args.input_image, args.mask
                )
            else:
                img_bytes, mime, usage = generate_openai(args.prompt, model, args.size, args.quality)
    except Exception as e:
        emit("STATUS", "error")
        emit("ERROR", str(e))
        return 1

    out_path = Path(args.output).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(img_bytes)

    emit("STATUS", "ok")
    emit("PATH", str(out_path))
    emit("BYTES", len(img_bytes))
    emit("MIME", mime)
    emit("PROVIDER", args.provider)
    emit("MODEL", model)
    emit("MODE", "edit" if edit_mode else "generate")
    if usage:
        emit("USAGE", json.dumps(usage))
    return 0


if __name__ == "__main__":
    sys.exit(main())
