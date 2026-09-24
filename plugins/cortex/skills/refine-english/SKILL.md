---
name: refine-english
description: Use when user shares text to refine for native English, asks for writing feedback, or asks how to pronounce a word - triggers on "refine this", "fix my English", "how do you pronounce", "check my writing", or when user pastes text that appears to be their own writing needing polish
model: sonnet
---

# Refine English

English writing coach that refines text to sound native and gives actionable feedback to improve over time.

## User Preferences

Load preferences at the start of every run:

1. If `${CLAUDE_PLUGIN_DATA}/preferences/refine-english.md` does not exist, seed it:
   ```bash
   mkdir -p "${CLAUDE_PLUGIN_DATA}/preferences"
   cp "${CLAUDE_PLUGIN_ROOT}/skills/refine-english/preferences.template.md" \
      "${CLAUDE_PLUGIN_DATA}/preferences/refine-english.md"
   ```
   Mention it once: "Seeded preferences at `${CLAUDE_PLUGIN_DATA}/preferences/refine-english.md` — edit anytime to customize."
2. Read it. Empty fields fall back to the defaults below:
   - `native_language` (default empty): when set, look for interference patterns typical of that language (literal translations, article or preposition habits) and, if the user writes to you in that language, explain in it.
   - `copy_to_clipboard` (default `false`): when `true`, copy the refined version to the clipboard (`pbcopy` on macOS, `xclip -selection clipboard` or `wl-copy` on Linux, `clip` on Windows).

## Modes

### 1. Text Refinement (default when the user shares text)

**Output format:**

#### Refined Version
> The polished text, ready to copy.

#### Changes Made
| Original | Refined | Why |
|----------|---------|-----|
| phrase | phrase | Brief explanation of the grammar/style/word choice fix |

#### Writing Tips
- 1-2 actionable tips based on **patterns** in the user's writing (not one-off typos)
- Focus on recurring habits: awkward phrasing, literal translations, article misuse, preposition errors, register mismatch
- Frame positively: "Native speakers tend to..." rather than "You got this wrong"

**Refinement principles:**
- Preserve the user's voice and intent; don't over-formalise
- Match the register (casual chat message vs professional email vs public post)
- Prefer natural, idiomatic phrasing over technically correct but stiff alternatives
- If context is unclear (who is this for?), ask before refining

### 2. Pronunciation Help (when the user asks "how do you pronounce X")

**Word:** the word
**IPA:** /phonetic transcription/
**Sounds like:** simple breakdown using familiar words ("rhymes with...", "sounds like...")
**Common mistake:** what non-native speakers often get wrong (tailor to `native_language` if set)
**Audio tip:** stress pattern marked (e.g., "em-PHA-sis on the first syllable")

### 3. Word/Phrase Suggestion (when the user asks "how do I say X naturally" or "what's a better word for X")

Give 2-3 options ranked by formality, with example sentences showing natural usage.

## Important Rules

- Keep feedback encouraging; the goal is improvement, not criticism
- Track recurring patterns across the conversation; if the user keeps making the same mistake, flag it explicitly: "I've noticed this pattern a few times now..."
