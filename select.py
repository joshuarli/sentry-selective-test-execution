# /// script
# dependencies = [
#   "matplotlib",
# ]
# ///

import os
import sqlite3
from typing import List, Set, Dict

import matplotlib.pyplot as plt
from collections import Counter


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


def affected_tests_for_file(conn: sqlite3.Connection, file_path: str) -> Dict[str, Set[int]]:
    """
    Returns a dictionary:
      test context -> set of executed line numbers in the given file.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT c.context, lb.numbits
        FROM line_bits lb
        JOIN file f    ON lb.file_id = f.id
        JOIN context c ON lb.context_id = c.id
        WHERE f.path LIKE ?
          AND c.context != ''
    """, (f"%/{file_path}",))

    results = {}
    for context, bitblob in cur.fetchall():
        lines = executed_lines(bitblob)
        if lines:
            results[context] = lines
    return results


if __name__ == "__main__":
    # source_files = [
    #     "src/sentry/preprod/size_analysis/compare.py",
    #     "src/sentry/preprod/size_analysis/download.py",
    #     "src/sentry/preprod/size_analysis/issues.py",
    #     "src/sentry/preprod/size_analysis/insight_models.py",
    #     "src/sentry/preprod/size_analysis/models.py",
    #     "src/sentry/preprod/size_analysis/tasks.py",
    #     "src/sentry/preprod/size_analysis/utils.py",
    # ]

    source_files = []
    reporoot = "/Users/josh/dev/sentry"

    for root, dirs, files in os.walk(f"{reporoot}/src/sentry"):
        for file in files:
            if not file.endswith(".py"):
                continue
            source_files.append(os.path.join(root, file)[len(reporoot)+1:])

    numbers_of_affected_test_files = []

    with sqlite3.connect("coverage.sqlite3") as conn:
        for file_path in source_files:
            test_lines = affected_tests_for_file(conn, file_path)
            test_files = {test_context.split("::")[0] for test_context in test_lines.keys()}
            print(f"{file_path}: {len(test_files)}")

            numbers_of_affected_test_files.append(len(test_files))

            # for test, lines in sorted(test_lines.items()):
            #    print(f"  {test}: {sorted(lines)}")

    counts = Counter(numbers_of_affected_test_files)
    x = list(counts.keys())
    y = list(counts.values())

    plt.bar(x, y)
    plt.xlabel("# selected test files")
    plt.ylabel("frequency")
    plt.title("distribution of single source file -> # selected test files")
    plt.show()


    # with sqlite3.connect("coverage.sqlite3") as conn:
    #     for file_path in source_files:
    #         test_lines = affected_tests_for_file(conn, file_path)
    #         print(f"\nSource file: {file_path}")
    #         if test_lines:
    #             print("Affected tests and executed lines:")
    #             for test, lines in sorted(test_lines.items()):
    #                 print(f"  {test}: {sorted(lines)}")
    #         else:
    #             print("  (No affected tests found)")
