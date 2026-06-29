#!/usr/bin/env python3
"""Benchmark all free OpenRouter models using the OpenAI-compatible API."""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from db_utils import write_run  # noqa: E402

API_BASE = "https://openrouter.ai/api/v1"
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_GROUP = os.getenv("MODEL_GROUP", "all")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))
PROMPT = "Write a Python function that checks if a number is prime and returns True or False"

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SCRIPT_DIR / "results.json"


def fetch_free_models() -> list[str]:
    """Return all free OpenRouter model IDs (pricing.prompt == pricing.completion == '0')."""
    request = urllib.request.Request(
        f"{API_BASE}/models",
        headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"Failed to fetch model list: {exc}", file=sys.stderr)
        return []

    free = []
    for model in data.get("data", []):
        pricing = model.get("pricing", {})
        prompt_price = str(pricing.get("prompt", "1"))
        completion_price = str(pricing.get("completion", "1"))
        if prompt_price == "0" and completion_price == "0":
            mid = model.get("id", "")
            if mid:
                free.append(mid)
    return sorted(free)


def selected_models(all_models: list[str]) -> list[str]:
    if MODEL_GROUP == "group1":
        half = len(all_models) // 2
        return all_models[:half]
    if MODEL_GROUP == "group2":
        half = len(all_models) // 2
        return all_models[half:]
    return all_models


def failure_result(model: str, error: str) -> dict[str, Any]:
    return {
        "model": model,
        "success": False,
        "error": error,
        "responseTime": None,
        "tokensGenerated": None,
        "totalTokens": None,
        "response": None,
    }


def normalize_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "".join(parts)
    return ""


def to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def call_model(model: str, prompt: str) -> dict[str, Any]:
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 500,
        "stream": False,
    }
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{API_BASE}/chat/completions",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/NIMStats",
            "X-Title": "NIMStats Benchmark",
        },
    )

    started = time.perf_counter()
    raw_body = ""
    status_code = 0

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status_code = response.status
            raw_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status_code = getattr(exc, "code", 0) or 0
        raw_body = exc.read().decode("utf-8", errors="replace")
    except TimeoutError:
        return failure_result(model, f"Request timed out after {REQUEST_TIMEOUT_SECONDS}s")
    except Exception as exc:
        return failure_result(model, f"Request failed: {exc}")

    response_time = int((time.perf_counter() - started) * 1000)

    if not raw_body.strip():
        return failure_result(model, "Empty response from API")

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return {
            "model": model,
            "success": False,
            "error": f"Invalid JSON response: {exc.msg}",
            "responseTime": response_time,
            "tokensGenerated": None,
            "totalTokens": None,
            "response": raw_body,
        }

    error_obj = data.get("error")
    error_message = ""
    if isinstance(error_obj, dict):
        error_message = str(error_obj.get("message") or "").strip()
    elif isinstance(error_obj, str):
        error_message = error_obj.strip()

    if status_code >= 400:
        error_message = f"HTTP {status_code}: {error_message}" if error_message else f"HTTP {status_code}"
        return failure_result(model, error_message)

    if error_message:
        return failure_result(model, error_message)

    choices = data.get("choices")
    content = ""
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            msg = first.get("message")
            if isinstance(msg, dict):
                content = normalize_content(msg.get("content"))

    if not content.strip():
        return failure_result(model, "No content in response")

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    return {
        "model": model,
        "success": True,
        "responseTime": response_time,
        "tokensGenerated": to_int(usage.get("completion_tokens")),
        "totalTokens": to_int(usage.get("total_tokens")),
        "response": content,
        "error": None,
    }


def compile_output(timestamp: str, prompt: str, models: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [m for m in models if m.get("success")]
    fastest_model, fastest_time = "N/A", 0
    if successful:
        fastest = min(successful, key=lambda m: m.get("responseTime") or float("inf"))
        fastest_model = fastest.get("model", "N/A")
        fastest_time = fastest.get("responseTime", 0) or 0
    return {
        "timestamp": timestamp,
        "prompt": prompt,
        "models": models,
        "summary": {
            "successCount": len(successful),
            "totalModels": len(models),
            "fastestModel": fastest_model,
            "fastestTime": fastest_time,
        },
    }


def main() -> int:
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY environment variable not set", file=sys.stderr)
        return 1

    print("Fetching free OpenRouter models...")
    all_free = fetch_free_models()
    if not all_free:
        print("No free models found or fetch failed.", file=sys.stderr)
        return 1

    models = selected_models(all_free)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    print(f"Starting OpenRouter free model benchmarks (group={MODEL_GROUP})...")
    print(f"Timestamp: {timestamp}")
    print(f"Total free models available: {len(all_free)}")
    print(f"Testing {len(models)} models in this group...")
    print()

    results: list[dict[str, Any]] = []
    for model in models:
        print(f"Testing: {model}")
        result = call_model(model, PROMPT)
        if result.get("success"):
            print(f"  OK ({result['responseTime']}ms, {result.get('tokensGenerated', 0)} tokens)")
        else:
            print(f"  FAIL: {result.get('error') or 'Unknown error'}")
        results.append(result)
        time.sleep(1.0)  # OpenRouter free tier rate limiting

    final_json = compile_output(timestamp, PROMPT, results)
    OUTPUT_FILE.write_text(json.dumps(final_json, indent=2), encoding="utf-8")

    sc = final_json["summary"]["successCount"]
    tc = final_json["summary"]["totalModels"]
    print(f"\nResults saved to {OUTPUT_FILE.name}")
    print(f"Summary: {sc}/{tc} successful")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
