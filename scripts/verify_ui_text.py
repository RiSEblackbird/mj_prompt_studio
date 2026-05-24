from __future__ import annotations

import re

from mj_prompt_studio.ui.strings import USER_VISIBLE_STRINGS

FORBIDDEN_PATTERNS = [
    re.compile(r"\bV\s*\d+(?:\.\d+)?\b"),
    re.compile(r"\bv\s*\d+(?:\.\d+)?\b"),
    re.compile(r"Version\s*\d+(?:\.\d+)?", re.IGNORECASE),
    re.compile(r"Midjourney\s+V\s*\d+(?:\.\d+)?", re.IGNORECASE),
]


def verify() -> None:
    violations = [
        text
        for text in USER_VISIBLE_STRINGS
        if any(pattern.search(text) for pattern in FORBIDDEN_PATTERNS)
    ]
    if violations:
        raise SystemExit(f"Forbidden user-visible version text: {violations}")


if __name__ == "__main__":
    verify()
