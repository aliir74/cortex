---
name: generate-image
description: "Generates or edits an image from a text description via OpenAI GPT Image (default) or Google Nano Banana: photoreal shots, illustrations, mockups, infographics, hero images. Use for 'generate/make/create an image of X', 'draw X', 'edit this image to X'. Saves to a configurable output folder (default ./generated-images/)."
---

# Generate Image

Single entry point for AI image generation and editing. Other skills can delegate to the script here, keeping prompt-craft in the calling skill while API, auth, and error handling live in one place.

## Prerequisites

Requires Python 3 (stdlib only) and an API key in the environment: `OPENAI_API_KEY` for the OpenAI provider, `GEMINI_API_KEY` for Gemini. If the needed key is not set, point the user to `SETUP.md` at the plugin root (section: **generate-image**) and stop until it's available.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/generate-image.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/generate-image/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/generate-image.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/generate-image.md` — edit anytime to customize."
2. Read it. Empty fields fall back to the defaults below:
   - `output_dir` (default `./generated-images/`): where images are saved; relative paths resolve against the current working directory.
   - `default_provider` (default `openai`), `default_model` (default: provider default below), `default_quality` (default `medium`).

## The contract: `generate.py`

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/generate-image/generate.py" \
  --prompt "<full prompt>" \
  --output "<path>.png" \
  [--provider openai|gemini]  \
  [--model <model-name>]      \
  [--quality low|medium|high] (openai)  \
  [--size WIDTHxHEIGHT]       (openai)  \
  [--aspect-ratio 1:1|4:3|3:4|16:9] (gemini) \
  [--input-image <path>] [--input-image <path>...] (edit mode) \
  [--mask <path>]            (openai edit only)
```

**Output is prefixed lines** the caller parses:
```
STATUS: ok | error
PATH: /abs/path
BYTES: N
MIME: image/png
PROVIDER: openai|gemini
MODEL: <model>
MODE: generate | edit
USAGE: <openai-token-usage-json>      (openai only)
ERROR: <message>                      (on failure)
```

## Providers and models

| Provider | Model | Cost (1024², medium) | Strengths |
|---|---|---|---|
| **openai** (default) | `gpt-image-1.5` | ~$0.05 | Strong photorealism, follows long structured prompts |
| openai | `gpt-image-2` | ~$0.05 | Top quality; requires OpenAI organisation verification |
| openai | `gpt-image-1-mini` | ~$0.01 | Drafts, thumbnails, iteration |
| openai | `dall-e-3` | ~$0.04 | Legacy; rarely better than image-1.5 |
| gemini | `gemini-2.5-flash-image` (Nano Banana) | ~$0.04 | Stylised illustrations, infographics |
| gemini | `gemini-3-pro-image-preview` (Nano Banana Pro) | ~$0.13 | Top-end Gemini, hi-fi text rendering |

Prices are approximate; check the provider's pricing page. **Default = OpenAI `gpt-image-1.5`** unless the user asks for Gemini or for top quality.

Auto-pick by intent:

| User intent | Provider | Model | Quality |
|---|---|---|---|
| Photorealistic product / scene / person / food | openai | `gpt-image-1.5` | medium |
| Hero shot, print-quality, billboard-size | openai | `gpt-image-2` (if verified) else 1.5 | high |
| Quick draft, exploring concepts | openai | `gpt-image-1-mini` | low |
| Stylised illustration, painterly, anime-ish | gemini | `gemini-2.5-flash-image` | n/a |
| Infographic / poster with embedded text | gemini | `gemini-3-pro-image-preview` | n/a |
| UI mockup of an app/site | openai | `gpt-image-1.5` | medium |
| Logo / icon | openai | `gpt-image-1.5` | medium |

## Edit mode (image-in, image-out)

When the user supplies a source image and asks to **modify, restyle, blend, extend, or inpaint** it, pass one or more `--input-image <path>` flags. The script routes to the provider's edit endpoint.

**Triggers:** "edit this image to X", "add/remove X", "restyle this in <style>", "blend these two images" (multiple `--input-image`), "use this as reference and …", "fill the masked area with X" (`--mask`, OpenAI only), continuing a previous generation ("now make it darker").

| Provider | Endpoint | Multi-image | Mask | Notes |
|---|---|---|---|---|
| **openai** (default) | `/v1/images/edits` | yes (sent as `image[]`) | yes (`--mask`, transparent = edit area) | Strong subject preservation |
| gemini | `generateContent` with inline image parts | yes | no | Best for stylised restyles and creative blends |

**Picking the provider for an edit:** faithful photoreal edit or mask inpaint/outpaint → openai; stylised restyle or blend → gemini; ambiguous → openai.

**Prompt style for edits:** be **delta-explicit**; describe only what changes and what stays. Examples:
- "Keep the cat, pose, and background identical. Add a small red knit hat tilted to the left. Match the existing lighting."
- "Restyle as flat 2D vector illustration. Preserve composition and subject placement. Palette: terracotta, sage, off-white."
- "Blend image 1's subject (the chair) into image 2's environment (the loft). Match the loft's light direction and grain."

**Output path for edits:** save next to the source with a `-edit` / `-v2` suffix when it's a clear iteration; otherwise use the standard output rule.

**Mask format (OpenAI inpaint):** PNG with an alpha channel, same dimensions as the input. Transparent pixels = edit, opaque = preserve. If the user describes a region instead of supplying a mask, prompt-only editing often works.

## Procedure

### 1. Build the prompt

Default to a **structured photographer / art-director brief**, not a single sentence. Both APIs perform much better with structure.

Generic template:
```
<shot type / framing> of <subject>, <key visible details>.
Style: <photography style | illustration style | flat vector | 3D render | etc.>.
Lighting: <natural soft window light | studio softbox | golden hour | dramatic side light>.
Background: <description, often "out of focus" for photos>.
Composition: <centered | rule-of-thirds | shallow DoF | flat lay>.
Colors: <palette cues>.
No text, no watermarks, no hands. <other negative prompts>.
```

**Illustration / editorial:**
```
Editorial illustration of <subject>, <style: flat geometric / collage / mid-century / line art with watercolor wash>.
Palette: <2-4 named colors>. Composition: <description>. Mood: <calm, energetic, melancholic>.
Aspect ratio: <ratio>. No text.
```

**Infographic / diagram** (use Gemini Nano Banana Pro for legible text):
```
Clean infographic about <topic>, <number> labeled sections arranged <horizontally | as a circular flow | in a 2x2 grid>.
Style: flat vector, <palette>, generous whitespace, sans-serif labels. Title at top: "<title>".
```

**UI mockup:**
```
Mobile app screen mockup for <feature>, <iOS | Android | web> design language.
Visible UI elements: <3-6 components>. Color scheme: <palette>. Device frame: <phone mockup | none>.
```

**Logo / icon:**
```
Minimal logo mark for <brand/concept>, <iconography description>.
Style: <flat 2D vector | geometric monogram | hand-drawn>. Single color: <hex or name>. White background, centered, generous padding.
No text unless requested. Vector-clean lines.
```

Strip filler words; lean on **concrete visual nouns and a defined style**.

### 2. Pick the output path

Default: `<output_dir>/YYYY-MM-DD-<slug>.png`, slug = 3-6 kebab-case words from the subject. If a calling skill provides a path, use it. If the file exists, append `-v2`, `-v3`; never silently overwrite.

### 3. Pick size / aspect ratio

| Use case | OpenAI `--size` | Gemini `--aspect-ratio` |
|---|---|---|
| Default / square | 1024x1024 | 1:1 |
| Landscape (blog hero, OG image, slide) | 1536x1024 | 16:9 |
| Portrait (mobile, story, vertical card) | 1024x1536 | 3:4 |
| Custom (gpt-image-2 only) | e.g. 1280x720 | n/a |

### 4. Call the script

Text-to-image:
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/generate-image/generate.py" \
  --prompt "<brief>" \
  --output "generated-images/YYYY-MM-DD-<slug>.png" \
  --quality medium
```

Edit an existing image (OpenAI):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/generate-image/generate.py" \
  --prompt "<delta-explicit brief>" \
  --input-image "generated-images/YYYY-MM-DD-cat.png" \
  --output "generated-images/YYYY-MM-DD-cat-edit.png"
```

Blend two images (Gemini):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/generate-image/generate.py" \
  --provider gemini \
  --prompt "<blend brief>" \
  --input-image "a.png" --input-image "b.png" \
  --output "generated-images/YYYY-MM-DD-blend.png"
```

Inpaint with a mask (OpenAI only):
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/skills/generate-image/generate.py" \
  --prompt "Fill the masked area with a leather armchair matching the room's lighting." \
  --input-image "room.png" --mask "armchair-mask.png" \
  --output "generated-images/YYYY-MM-DD-room-armchair.png"
```

Parse `STATUS:`. On success, read `PATH:`, `MODE:`, and `USAGE:`.

### 5. Handle errors

| Signature | Cause | Action |
|---|---|---|
| `403 ... organization must be verified` | OpenAI org not verified for `gpt-image-2` | Point to OpenAI organisation settings; offer `gpt-image-1.5`. **Do not loop.** |
| `401 ... Incorrect API key` | Missing/expired key | Tell the user to update `OPENAI_API_KEY` |
| `insufficient_quota` | OpenAI billing/cap | Point to the OpenAI billing page |
| `RESOURCE_EXHAUSTED` (Gemini) | No image quota on the Gemini key | Point to Google AI Studio billing; offer `--provider openai` |
| Safety refusal | Model refused | Show the refusal text, ask the user to adjust the prompt |
| Other network/HTTP | Transient | Retry once; if still failing, stop and report |

### 6. Report to the user

- The absolute path (open it for review when running on a desktop: `open` / `xdg-open`)
- Provider/model used + approximate cost from `USAGE:`
- The next cheaper/pricier tier if they want to A/B

To regenerate, **vary the prompt** (framing, palette, or style) and save as `-v2`; the same prompt gives near-identical output.

Don't auto-embed the image into documents; the user usually wants to inspect it first.

## Common mistakes

| Mistake | Fix |
|---|---|
| Single-sentence prompt "an image of X" | Always use the structured brief |
| Defaulting to `gpt-image-2` | Use `gpt-image-1.5` unless the user asks for top quality and the org is verified |
| Asking "what model?" instead of inferring | Pick by the intent table; ask only if genuinely ambiguous |
| Running without the provider's API key exported | Check `OPENAI_API_KEY` / `GEMINI_API_KEY` first |
| Overwriting an earlier generation | Bump `-v2`, `-v3` if the path exists |
| Retrying on a verification 403 | Offer the fallback model; do not loop |
| Promising text rendering in OpenAI output | OpenAI image models still mangle complex text; route text-heavy work to `gemini-3-pro-image-preview` |
| Naming certain controversial artists in OpenAI prompts | Some artist names trip the safety filter even for benign prompts; describe the visual qualities (materials, texture, palette) instead. Gemini is often more permissive |

## For skill authors

A domain skill that needs image generation should build its own prompt, pick its own output path, shell out to `generate.py`, and parse `STATUS:`. Do not re-implement provider switching, auth, error handling, or model selection; the script is the contract.
