#!/usr/bin/env python3
"""archive-plan-html.py <plan-path>

Marks the hero status as 'done' and moves the HTML plan to <parent>/done/.
Prints the new absolute path.
"""

import pathlib
import re
import shutil
import sys


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <plan-path>", file=sys.stderr)
        sys.exit(2)

    plan_path = pathlib.Path(sys.argv[1])
    if not plan_path.is_file():
        print(f"error: plan not found: {plan_path}", file=sys.stderr)
        sys.exit(2)

    text = plan_path.read_text()
    new = re.sub(
        r'(<header class="hero" data-status=")(planning|in_progress)(")',
        lambda m: m.group(1) + "done" + m.group(3),
        text,
        count=1,
    )
    plan_path.write_text(new)

    done_dir = plan_path.parent / "done"
    done_dir.mkdir(parents=True, exist_ok=True)
    dest = done_dir / plan_path.name
    shutil.move(str(plan_path), str(dest))
    print(dest.resolve())


if __name__ == "__main__":
    main()
