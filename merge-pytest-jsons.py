#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from collections import defaultdict


def extract_duration(test):
    if "duration" in test and isinstance(test["duration"], (int, float)):
        return test["duration"]

    call = test.get("call")
    if isinstance(call, dict) and isinstance(call.get("duration"), (int, float)):
        return call["duration"]

    return None


def main(paths):
    merged = {}
    stats = defaultdict(lambda: {
        "nodeid": None,
        "runs": 0,
        "total_duration": 0.0,
        "min_duration": None,
        "max_duration": None,
    })

    for path in paths:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        tests = data.get("tests")
        if not isinstance(tests, list):
            raise RuntimeError(f"{path}: missing or invalid 'tests' list")

        for test in tests:
            nodeid = test.get("nodeid") or test.get("id")
            if not nodeid:
                continue

            duration = extract_duration(test)
            if duration is None:
                continue

            s = stats[nodeid]
            s["nodeid"] = nodeid
            s["runs"] += 1
            s["total_duration"] += duration
            s["min_duration"] = (
                duration if s["min_duration"] is None
                else min(s["min_duration"], duration)
            )
            s["max_duration"] = (
                duration if s["max_duration"] is None
                else max(s["max_duration"], duration)
            )

    merged_tests = []
    for s in stats.values():
        merged_tests.append({
            "nodeid": s["nodeid"],
            "runs": s["runs"],
            "total_duration": s["total_duration"],
            "avg_duration": s["total_duration"] / s["runs"],
            "min_duration": s["min_duration"],
            "max_duration": s["max_duration"],
        })

    merged_tests.sort(key=lambda t: t["total_duration"], reverse=True)

    merged = {
        "summary": {
            "unique_tests": len(merged_tests),
            "total_runs": sum(t["runs"] for t in merged_tests),
            "total_duration": sum(t["total_duration"] for t in merged_tests),
        },
        "tests": merged_tests,
    }

    json.dump(merged, sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: merge_pytest_jsons.py pytest1.json pytest2.json ...",
              file=sys.stderr)
        sys.exit(1)

    main([Path(p) for p in sys.argv[1:]])
