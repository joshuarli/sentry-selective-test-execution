#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from collections import defaultdict


def main(path: Path, prefix: str):
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    tests = data.get("tests")
    if not isinstance(tests, list):
        raise RuntimeError("Expected top-level 'tests' list")

    totals = defaultdict(float)

    for test in tests:
        nodeid = test.get("nodeid")
        if not nodeid:
            continue

        total_duration = test.get("total_duration")
        if not isinstance(total_duration, (int, float)):
            continue

        # File path is everything before first ::
        file_path = nodeid.split("::", 1)[0]

        if prefix and not file_path.startswith(prefix):
            continue

        totals[file_path] += total_duration

    if not totals:
        raise RuntimeError("No matching tests found")

    # Sort slowest files first
    for file_path, duration in sorted(
        totals.items(), key=lambda x: x[1], reverse=True
    ):
        print(f"{duration:10.3f}s  {file_path}")


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(
            "Usage: pytest_file_durations.py pytest.json [file_prefix]",
            file=sys.stderr,
        )
        sys.exit(1)

    json_path = Path(sys.argv[1])
    prefix = sys.argv[2] if len(sys.argv) == 3 else None

    main(json_path, prefix)
