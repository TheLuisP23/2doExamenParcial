"""ISBN-13 (REQ-A-001, REQ-A-007)."""

from __future__ import annotations

import re


def normalize_isbn(raw: str) -> str:
    return re.sub(r"[\s-]", "", raw)


def is_valid_isbn13(isbn: str) -> bool:
    if not re.fullmatch(r"97[89]\d{10}", isbn):
        return False
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn[:12]))
    return (10 - total % 10) % 10 == int(isbn[12])
