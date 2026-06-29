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
from quality import TEST_PROMPTS, compute_quality  # noqa: E402

API_BASE = "https://openrouter.ai/api/v1"
API_KEY = os.getenv("OPENROUTER_API_KEY", "")
MODEL_GROUP = os.getenv("MODEL_GROUP", "all")
REQUEST_TIMEOUT_SECONDS = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "120"))

SCRIPT_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = SCRIPT_DIR / "results.json"


def fetch_free_models() -> list[str]:
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
        if str(pricing.get("prompt", "1")) == "0" and str(pricing.get("completion", "1")) == "0":
            mid = model.get("id", "")
            if mid:
                free.append(mid)
    return sorted(free)


def selected_models(all_models: list[str]) -> list[str]:
    if MODEL_GROUP == "group1":
        return all_models[: len(all_models) // 2]
    if MODEL_GROUP == "group2":
        return all_models[len(all_models) // 2 :]
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
        "qualityScore": None,
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


def call_api(model: str, prompt: str) -> tuple[bool, str, int, int, int, str]:
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
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
            status_code = resp.status
            raw_body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status_code = getattr(exc, "code", 0) or 0
        raw_body = exc.read().decode("utf-8", errors="replace")
    except TimeoutError:
        return False, "", 0, 0, 0, f"Request timed out after {REQUEST_TIMEOUT_SECONDS}s"
    except Exception as exc:
        return False, "", 0, 0, 0, f"Request failed: {exc}"

    response_time = int((time.perf_counter() - started) * 1000)

    if not raw_body.strip():
        return False, "", response_time, 0, 0, "Empty response from API"

    try:
        data = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        return False, "", response_time, 0, 0, f"Invalid JSON: {exc.msg}"

    error_obj = data.get("error")
    error_message = ""
    if isinstance(error_obj, dict):
        error_message = str(error_obj.get("message") or "").strip()
    elif isinstance(error_obj, str):
        error_message = error_obj.strip()

    if status_code >= 400:
        msg = f"HTTP {status_code}: {error_message}" if error_message else f"HTTP {status_code}"
        return False, "", response_time, 0, 0, msg

    if error_message:
        return False, "", response_time, 0, 0, error_message

    choices = data.get("choices")
    content = ""
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            msg = first.get("message")
            if isinstance(msg, dict):
                content = normalize_content(msg.get("content"))

    if not content.strip():
        return False, "", response_time, 0, 0, "No content in response"

    usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
    return True, content, response_time, to_int(usage.get("completion_tokens")), to_int(usage.get("total_tokens")), ""


def benchmark_model(model: str) -> dict[str, Any]:
    responses: list[str] = []
    first_success = False
    first_error = ""
    first_time = None
    first_completion = 0
    first_total = 0

    for i, prompt in enumerate(TEST_PROMPTS):
        ok, content, rt, comp, total, err = call_api(model, prompt)
        if i == 0:
            first_success = ok
            first_error = err
            first_time = rt
            first_completion = comp
            first_total = total
        responses.append(content if ok else "")
        if i < len(TEST_PROMPTS) - 1:
            time.sleep(1.0)  # rate limit buffer

    if not first_success:
        return failure_result(model, first_error)

    quality = compute_quality(responses)

    return {
        "model": model,
        "success": True,
        "responseTime": first_time,
        "tokensGenerated": first_completion,
        "totalTokens": first_total,
        "response": responses[0] if responses else None,
        "error": None,
        "qualityScore": quality["quality_score"],
        "qualityBreakdown": quality["quality_breakdown"],
    }


def compile_output(timestamp: str, models: list[dict[str, Any]]) -> dict[str, Any]:
    successful = [m for m in models if m.get("success")]
    fastest_model, fastest_time = "N/A", 0
    if successful:
        fastest = min(successful, key=lambda m: m.get("responseTime") or float("inf"))
        fastest_model = fastest.get("model", "N/A")
        fastest_time = fastest.get("responseTime", 0) or 0
    return {
        "timestamp": timestamp,
        "prompt": TEST_PROMPTS[0],
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
    print(f"OpenRouter benchmark (group={MODEL_GROUP}) - {len(models)} models, {len(TEST_PROMPTS)} tests each")
    print(f"Timestamp: {timestamp}\n")

    results: list[dict[str, Any]] = []
    for model in models:
        print(f"Testing: {model}")
        result = benchmark_model(model)
        if result.get("success"):
            q = result.get("qualityScore", 0)
            print(f"  OK  {result['responseTime']}ms  quality={q}/100")
        else:
            print(f"  FAIL: {result.get('error') or 'Unknown error'}")
        results.append(result)
        time.sleep(1.0)

    final_json = compile_output(timestamp, results)
    OUTPUT_FILE.write_text(json.dumps(final_json, indent=2), encoding="utf-8")
    sc = final_json["summary"]["successCount"]
    tc = final_json["summary"]["totalModels"]
    print(f"\nResults saved. Summary: {sc}/{tc} successful")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
