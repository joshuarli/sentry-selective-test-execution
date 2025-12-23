#!/usr/bin/env python3

import json
import sys
from pathlib import Path


def extract_duration(test):
    """
    Return a representative duration for sorting/printing.

    Priority:
    1. merged format: total_duration
    2. raw format: duration
    3. raw format: call.duration
    """
    if isinstance(test.get("total_duration"), (int, float)):
        return test["total_duration"]

    if isinstance(test.get("duration"), (int, float)):
        return test["duration"]

    call = test.get("call")
    if isinstance(call, dict) and isinstance(call.get("duration"), (int, float)):
        return call["duration"]

    return None


def main(path: Path):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tests = data.get("tests")
    if not isinstance(tests, list):
        raise RuntimeError("Expected top-level 'tests' list")

    rows = []
    for test in tests:
        nodeid = test.get("nodeid") or test.get("id")
        if not nodeid:
            continue

        duration = extract_duration(test)
        if duration is None:
            continue

        rows.append((nodeid, duration, test))

    if not rows:
        raise RuntimeError("No test durations found in pytest.json")

    # Sort slowest first
    rows.sort(key=lambda r: r[1], reverse=True)

    for nodeid, duration, test in rows:
        runs = test.get("runs", 1)
        print(f"{duration:8.3f}s  runs={runs:<3}  {nodeid}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: pytest-times.py pytest.json", file=sys.stderr)
        sys.exit(1)

    main(Path(sys.argv[1]))
