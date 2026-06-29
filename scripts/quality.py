#!/usr/bin/env python3
"""Quality scoring for benchmark responses.

Three tests, each weighted:
  code  (40pts) - extract and execute the is_prime function
  math  (30pts) - 17 x 23 = 391
  logic (30pts) - snail-in-well = 8 days
"""

import re
import subprocess
from typing import Any


# ── Test prompts ──────────────────────────────────────────────────────────────

CODE_PROMPT = (
    "Write a Python function named `is_prime` that takes a single integer "
    "argument and returns True if the number is prime and False otherwise. "
    "Return only the function definition with no explanation, imports, or example usage."
)

MATH_PROMPT = (
    "What is 17 multiplied by 23? Reply with only the integer result, nothing else."
)

LOGIC_PROMPT = (
    "A snail is at the bottom of a 10-foot well. Each day it climbs 3 feet, "
    "but each night it slides back 2 feet. How many days does it take for the "
    "snail to reach the top of the well? Reply with only the integer number of days."
)

TEST_PROMPTS = [CODE_PROMPT, MATH_PROMPT, LOGIC_PROMPT]


# ── Validators ────────────────────────────────────────────────────────────────

_CODE_CASES = [
    (2, True), (3, True), (4, False), (7, True), (9, False),
    (13, True), (1, False), (0, False), (17, True), (25, False),
]


def _extract_function(text: str) -> str:
    """Pull the first Python function block out of a model response."""
    # Strip markdown code fences
    fenced = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)

    # Find `def is_prime` and grab until the next top-level def/class or EOF
    match = re.search(r"(def is_prime\b.*?)(?=\ndef |\nclass |\Z)", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return ""


def score_code(response: str) -> float:
    """Return fraction of test cases passed (0.0-1.0)."""
    code = _extract_function(response)
    if not code:
        return 0.0

    cases_code = "\n".join(
        f"_results.append(is_prime({n}) == {str(exp)})"
        for n, exp in _CODE_CASES
    )
    script = f"{code}\n\n_results = []\n{cases_code}\nprint(sum(_results))"

    try:
        proc = subprocess.run(
            ["python3", "-c", script],
            capture_output=True, text=True, timeout=5,
        )
        passed = int(proc.stdout.strip())
        return passed / len(_CODE_CASES)
    except Exception:
        return 0.0


def score_number(response: str, expected: int) -> float:
    """Return 1.0 if the first integer in the response matches expected."""
    nums = re.findall(r"\b\d+\b", response.strip())
    if nums and int(nums[0]) == expected:
        return 1.0
    return 0.0


# ── Combined scorer ───────────────────────────────────────────────────────────

_TESTS = [
    ("code",  40, lambda r: score_code(r)),
    ("math",  30, lambda r: score_number(r, 391)),
    ("logic", 30, lambda r: score_number(r, 8)),
]


def compute_quality(responses: list[str]) -> dict[str, Any]:
    """
    responses: [code_response, math_response, logic_response]
    Returns dict with quality_score (0-100) and per-test breakdown.
    """
    if len(responses) < len(_TESTS):
        responses = responses + [""] * (len(_TESTS) - len(responses))

    breakdown: dict[str, float] = {}
    total = 0.0
    for (tid, weight, fn), resp in zip(_TESTS, responses):
        frac = fn(resp) if resp else 0.0
        pts = round(frac * weight, 1)
        breakdown[tid] = pts
        total += pts

    return {
        "quality_score": round(total),
        "quality_breakdown": breakdown,
    }
