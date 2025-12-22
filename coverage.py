import sys
import sqlite3
from typing import Dict, Set

def executed_lines(bitblob: bytes) -> Set[int]:
    lines = set()
    for byte_index, byte in enumerate(bitblob):
        for bit_index in range(8):
            if byte & (1 << bit_index):
                lines.add(byte_index * 8 + bit_index)
    return lines

def get_test_file_info(conn: sqlite3.Connection, substring=""):
    """
    Returns a list of tuples:
        (test_context, num_files, {file_path -> bitblob})
    Ordered by num_files descending.
    """
    cur = conn.cursor()

    cur.execute("""
        SELECT c.context, COUNT(DISTINCT f.id) as num_files
        FROM line_bits lb
        JOIN file f ON lb.file_id = f.id
        JOIN context c ON lb.context_id = c.id
        WHERE c.context != ''
          AND c.context LIKE ?
        GROUP BY c.context
        ORDER BY num_files DESC
    """, (f"%{substring}%",))
    counts = cur.fetchall()

    test_info = []
    for context, num_files in counts:
        cur.execute("""
            SELECT f.path, lb.numbits
            FROM line_bits lb
            JOIN file f ON lb.file_id = f.id
            JOIN context c ON lb.context_id = c.id
            WHERE c.context = ?
        """, (context,))
        mapping = {file_path: bitblob for file_path, bitblob in cur.fetchall() if bitblob}
        test_info.append((context, num_files, mapping))

    return test_info

if __name__ == "__main__":
    # python3 coverage.py 'tests/sentry/test_wsgi.py'
    # this example covers the majority of py files in src/sentry which makes sense

    conn = sqlite3.connect("coverage.sqlite3")

    test_coverage = get_test_file_info(conn, substring=sys.argv[1])

    for test, num_files, mapping in test_coverage:
        print(f"\n{test}")
        if mapping:
            print("coverage:")
            for file_path, bitblob in mapping.items():
                lines = sorted(executed_lines(bitblob))
                print(f"  {file_path}: {lines}")
        else:
            print("  (No executed lines found)")

    conn.close()
