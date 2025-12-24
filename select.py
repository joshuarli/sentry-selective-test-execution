# /// script
# dependencies = [
#   "matplotlib",
# ]
# ///

import os
import sqlite3
from typing import List, Set, Dict


def executed_lines(bitblob: bytes) -> Set[int]:
    """
    Returns a set of executed line numbers for a coverage bitblob.
    Line numbers are 1-based.
    """
    lines = set()
    for byte_index, byte in enumerate(bitblob):
        for bit_index in range(8):
            if byte & (1 << bit_index):
                lines.add(byte_index * 8 + bit_index)
    return lines


def affected_tests_for_files(conn: sqlite3.Connection, file_paths: list[str]) -> dict[str, set[int]]:
    placeholders = ",".join("?" for _ in file_paths)

    cur = conn.cursor()
    cur.execute(
        f"""
        SELECT c.context, lb.numbits
        FROM line_bits lb
        JOIN file f    ON lb.file_id = f.id
        JOIN context c ON lb.context_id = c.id
        WHERE f.path IN ({placeholders})
          AND c.context != ''
        """,
        file_paths,
    )

    results: dict[str, Set[int]] = {}

    for test_context, bitblob in cur.fetchall():
        if not test_context.endswith("|run"):
            # for now we're ignoring |setup and |teardown
            continue

        lines = executed_lines(bitblob)
        if not lines:
            continue

        test_id = test_context.partition("|")[0]

        if test_id in results:
            results[test_id].update(lines)
        else:
            results[test_id] = set(lines)

    return results


if __name__ == "__main__":
    # we'll need this for backend PR simulations as they touch multiple files
    #with sqlite3.connect("coverage.sqlite3") as conn:
    #    affected_tests = affected_tests_for_files(conn, [f"{reporoot}/src/sentry/preprod/size_analysis/compare.py", "{reporoot}/src/sentry/preprod/size_analysis/download.py"])

    source_files = []
    reporoot = "/Users/josh/dev/sentry"

    for root, dirs, files in os.walk(f"{reporoot}/src/sentry"):
        for filename in files:
            if not filename.endswith(".py"):
                continue

            abs_path = os.path.abspath(os.path.join(root, filename))
            # TODO: file paths in coverage are absolute so we'll have to
            #       change to relative to sentry reporoot when we get there
            source_files.append("/home/runner/work/sentry/sentry" + abs_path[len(reporoot):])

    numbers_of_affected_tests = []

    with sqlite3.connect("coverage.sqlite3") as conn:
        for file_path in source_files:
            affected_tests = affected_tests_for_files(conn, (file_path,))

            #for test_id in affected_tests.keys():
                # TODO determine total duration of affected tests

            print(f"{file_path}: {len(affected_tests)}")
            numbers_of_affected_tests.append(len(affected_tests))


    import matplotlib.pyplot as plt
    from collections import Counter

    counts = Counter(numbers_of_affected_tests)
    x = list(counts.keys())
    y = list(counts.values())

    plt.bar(x, y)
    plt.xlabel("# selected tests")
    plt.ylabel("frequency")
    plt.title("distribution of single source file -> # selected tests")
    plt.show()
