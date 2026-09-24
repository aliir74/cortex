# Operations reference (how-to-html)

Read this at step 4, after the HTML file exists: opening the artifact and linking it back to its task. Nothing here is needed while writing the page.

## Auto-open

Open the file in the OS default browser so the user sees it immediately. The **only** skip condition is `$HTML_NO_OPEN` being set; when it is, print the absolute path instead.

```bash
# macOS: open · Linux: xdg-open
if [ -z "$HTML_NO_OPEN" ]; then
  if command -v open >/dev/null; then open "$PATH_TO_HTML"; else xdg-open "$PATH_TO_HTML"; fi
else
  echo "$PATH_TO_HTML"
fi
```

Chained skills (a plan-then-execute wrapper, for example) set `$HTML_NO_OPEN` / `$PLAN_NO_OPEN` so the outer skill controls opening. Don't `open` from inside a skill wrapped by a chain. A genuinely headless or CI context sets the variable itself, so don't skip on a hunch.

## Link the artifact back to its task

A persistent artifact (plan, prep doc, report, deck) should be discoverable from the task it was generated for. If the work is tied to a tracked task (an issue, a ticket, a task line in a notes file), add the artifact's path to that task's record, labelled with the artifact's own descriptive name (its slug or title), not a category word like `plan`.

**Only link when a related task actually exists** and this artifact was generated for it. Never invent one, never append to an unrelated task, and skip if the path is already linked.

## Rationalizations

| Excuse | Reality |
|---|---|
| "It's a background session, so auto-open is pointless" | The only skip condition is `$HTML_NO_OPEN`, which a genuinely headless context sets itself. Do not skip on a hunch. |
| "The verifier said deterministic passed, so it renders correctly" | It does not follow. `verify_diagrams.py` checks viewBox geometry and cannot see CSS. The class-coverage check is the counterpart that catches missing chart CSS. Report the deterministic result as exactly that, never as "it looks right". |
