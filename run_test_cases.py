#!/usr/bin/env python3
"""
Run test cases from test_cases.json against the API.
Requires API server running: python main.py
"""

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)


def load_test_cases() -> dict:
    path = Path(__file__).parent / "test_cases.json"
    with open(path) as f:
        return json.load(f)


def run_tests(api_url: str = "http://localhost:8000") -> tuple[int, int]:
    data = load_test_cases()
    cases = data["test_cases"]
    passed = 0
    failed = 0

    print("=" * 60)
    print(f"Running {len(cases)} test cases against {api_url}")
    print("=" * 60)

    for tc in cases:
        tid = tc["id"]
        name = tc["name"]
        method = tc.get("method", "GET")
        endpoint = tc.get("endpoint", "/")
        url = f"{api_url.rstrip('/')}{endpoint}"
        expected_status = tc.get("expected_status", 200)

        try:
            if method == "GET":
                resp = requests.get(url, timeout=30)
            else:
                payload = tc.get("payload", {})
                resp = requests.post(url, json=payload, timeout=60)

            status_ok = resp.status_code == expected_status
            type_ok = True
            keys_ok = True

            if status_ok and resp.status_code == 200:
                j = resp.json()
                if "expected_type" in tc and "type" in j:
                    type_ok = j.get("type") == tc["expected_type"]
                if "expected_response_keys" in tc:
                    keys_ok = all(k in j for k in tc["expected_response_keys"])

            ok = status_ok and type_ok and keys_ok
            if ok:
                passed += 1
                print(f"  {tid} {name}: ✅ PASS")
            else:
                failed += 1
                reasons = []
                if not status_ok:
                    reasons.append(f"status {resp.status_code} != {expected_status}")
                if not type_ok:
                    reasons.append("type mismatch")
                if not keys_ok:
                    reasons.append("missing response keys")
                print(f"  {tid} {name}: ❌ FAIL ({', '.join(reasons)})")
                if resp.status_code == 200:
                    print(f"      Response: {resp.text[:200]}...")

        except requests.exceptions.ConnectionError:
            failed += 1
            print(f"  {tid} {name}: ❌ FAIL (Connection refused - is API running?)")
        except Exception as e:
            failed += 1
            print(f"  {tid} {name}: ❌ FAIL ({e})")

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    return passed, failed


if __name__ == "__main__":
    api_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    passed, failed = run_tests(api_url)
    sys.exit(0 if failed == 0 else 1)
