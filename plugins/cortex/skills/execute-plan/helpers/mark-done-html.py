#!/usr/bin/env python3
"""mark-done-html.py <plan-path> <unique-substring>

Flips the first matching pending step to done in an HTML plan:
- `data-status="pending"` → `data-status="done"` on the `<li class="step">`
- Adds `checked` to the inner `<input>`
- Recomputes the parent `<article>`'s data-task-status if all its steps are done
- Recomputes the hero data-status if every task is done

Errors on zero or multiple matches (matches the markdown helper's contract).
"""

import html as html_mod
import pathlib
import re
import sys


STEP_RE = re.compile(
    r'(<li class="step" data-status=")pending("[^>]*>\s*'
    r'<input type="checkbox")(\s*/>\s*'
    r'<span class="step-text">(.*?)</span>\s*</li>)',
    re.DOTALL,
)


def strip_tags(s: str) -> str:
    return html_mod.unescape(re.sub(r"<[^>]+>", "", s))


def main() -> None:
    if len(sys.argv) != 3:
        print(f"usage: {sys.argv[0]} <plan-path> <unique-substring>", file=sys.stderr)
        sys.exit(2)

    plan_path = pathlib.Path(sys.argv[1])
    needle = sys.argv[2]
    if not plan_path.is_file():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        sys.exit(2)

    text = plan_path.read_text()
    needle_norm = needle.replace("`", "").lower()

    matches: list[tuple[int, re.Match]] = []
    for m in STEP_RE.finditer(text):
        step_text = strip_tags(m.group(4)).lower()
        if needle_norm in step_text:
            matches.append((m.start(), m))

    if not matches:
        print(f"error: no pending step matches {needle!r}", file=sys.stderr)
        sys.exit(1)
    if len(matches) > 1:
        print(
            f"error: {len(matches)} pending steps match {needle!r}; be more specific",
            file=sys.stderr,
        )
        for _, m in matches:
            print(f"  - {strip_tags(m.group(4)).strip()[:120]}", file=sys.stderr)
        sys.exit(1)

    _, m = matches[0]
    replaced = m.group(1) + "done" + m.group(2) + " checked" + m.group(3)
    text = text[: m.start()] + replaced + text[m.end():]

    # Recompute task & hero status.
    text = recompute_task_status(text)
    text = recompute_hero_status(text)

    plan_path.write_text(text)
    print(f"marked: {strip_tags(m.group(4)).strip()[:120]}")


def recompute_task_status(text: str) -> str:
    """For each <article class="task">, set data-task-status based on its steps."""
    task_re = re.compile(
        r'(<article class="task" data-task-id="[^"]+" data-task-status=")'
        r'(pending|done)("[^>]*>)(.*?)(</article>)',
        re.DOTALL,
    )

    def fix(m: re.Match) -> str:
        body = m.group(4)
        pending = re.search(r'data-status="pending"', body)
        new_status = "pending" if pending else "done"
        return m.group(1) + new_status + m.group(3) + body + m.group(5)

    return task_re.sub(fix, text)


def recompute_hero_status(text: str) -> str:
    """Set hero data-status to 'done' if every step is done; otherwise leave as-is
    unless it's currently 'planning' AND any step is done → bump to 'in_progress'."""
    any_pending = bool(re.search(r'<li class="step" data-status="pending"', text))
    any_done = bool(re.search(r'<li class="step" data-status="done"', text))

    hero_re = re.compile(r'(<header class="hero" data-status=")(planning|in_progress|done)(")')

    if not any_pending and any_done:
        return hero_re.sub(lambda m: m.group(1) + "done" + m.group(3), text)
    if any_done:
        # bump planning → in_progress
        return hero_re.sub(
            lambda m: m.group(1) + ("in_progress" if m.group(2) == "planning" else m.group(2)) + m.group(3),
            text,
        )
    return text


if __name__ == "__main__":
    main()
