import re


INSUFFICIENT_PATTERNS = [
    re.compile(r"\binsufficient\b", re.IGNORECASE),
    re.compile(r"\bnsf\b", re.IGNORECASE),
    re.compile(r"\bnot\s+sufficient\s+funds\b", re.IGNORECASE),
]


def classify_decline(result_text: str) -> str:
    if not result_text:
        return "unknown"

    for pattern in INSUFFICIENT_PATTERNS:
        if pattern.search(result_text):
            return "insufficient_funds"

    return "do_not_retry"
