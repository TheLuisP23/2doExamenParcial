#!/usr/bin/env python3
"""Hook commit-msg: exige Conventional Commits. Uso: check_commit_msg.py <archivo-mensaje>"""

from __future__ import annotations

import re
import sys

TYPES = "feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert"
PATTERN = re.compile(rf"^({TYPES})(\([a-z0-9][a-z0-9-]*\))?!?: \S.{{0,99}}$")


def main() -> int:
    msg = open(sys.argv[1], encoding="utf-8").read()
    first = next((line for line in msg.splitlines() if line.strip() and not line.startswith("#")), "")
    if first.startswith(("Merge ", 'Revert "', "fixup! ", "squash! ")) or PATTERN.match(first):
        return 0
    print(
        f"✗ mensaje no cumple Conventional Commits: {first!r}\n"
        f"  formato: <tipo>(<ámbito>)?: <descripción>   tipos: {TYPES.replace('|', ', ')}\n"
        "  ejemplo: feat(a): crear libro [TASK-A-09]",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
