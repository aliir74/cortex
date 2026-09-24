#!/usr/bin/env python3
"""next-task-html.py <plan-path>

Prints the next pending step from an HTML plan in the same format as
the markdown version, so the execute-plan workflow mirrors execute-plan-md.

Output:
  TASK: Task 1.1: Foo
  FILES:
    - Create: path/to/foo.py
  STEP: - [ ] Step text

Exit 0 if a step was printed, 1 if all steps are done.
"""

import pathlib
import re
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <plan-path>", file=sys.stderr)
        sys.exit(2)

    plan_path = pathlib.Path(sys.argv[1])
    if not plan_path.is_file():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        sys.exit(2)

    html_text = plan_path.read_text()

    # Find all tasks (with their offsets) so we can locate the parent task
    # of a pending step by string position.
    task_re = re.compile(
        r'<article class="task"[^>]*data-task-id="([^"]+)"[^>]*>(.*?)</article>',
        re.DOTALL,
    )
    name_re = re.compile(r'<span class="task-name">(.*?)</span>', re.DOTALL)
    files_re = re.compile(r'<div class="files">(.*?)</div>', re.DOTALL)
    pending_step_re = re.compile(
        r'<li class="step" data-status="pending"[^>]*>\s*'
        r'<input type="checkbox"[^>]*/>\s*'
        r'<span class="step-text">(.*?)</span>\s*</li>',
        re.DOTALL,
    )

    for m in task_re.finditer(html_text):
        task_id = m.group(1)
        body = m.group(2)
        first = pending_step_re.search(body)
        if not first:
            continue

        name_m = name_re.search(body)
        task_name = strip_tags(name_m.group(1)).strip() if name_m else ""
        files_m = files_re.search(body)
        files_inline = strip_tags(files_m.group(1)).strip() if files_m else ""
        files_inline = re.sub(r"^\s*Files\s*", "", files_inline, count=1).strip()

        step_text = strip_tags(first.group(1)).strip()
        print(f"TASK: Task {task_id}: {task_name}")
        print("FILES:")
        if files_inline:
            for piece in files_inline.split(" · "):
                p = piece.strip()
                if p:
                    print(f"  - {p}")
        else:
            print("  - (none specified)")
        print(f"STEP: - [ ] {step_text}")
        return

    sys.exit(1)


def strip_tags(s: str) -> str:
    import html as html_mod
    no_tags = re.sub(r"<[^>]+>", "", s)
    return html_mod.unescape(no_tags)


if __name__ == "__main__":
    main()
