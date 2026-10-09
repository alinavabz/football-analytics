"""Measure the analyst queries in sql/queries/ with EXPLAIN ANALYZE.

Each query runs once to warm the cache, then several more times; the median execution time is
reported along with how each table was read (sequential scan or which index).
"""

import argparse
import json
import statistics
from pathlib import Path

from football_analytics.config import PostgresSettings

QUERY_DIR = Path(__file__).resolve().parents[2] / "sql" / "queries"


def scans(plan: dict) -> list[str]:
    """Every table access in a plan tree, e.g. 'Seq Scan on events'."""
    found = []
    if "Relation Name" in plan:
        index = f" using {plan['Index Name']}" if "Index Name" in plan else ""
        found.append(f"{plan['Node Type']}{index} on {plan['Relation Name']}")
    for child in plan.get("Plans", []):
        found.extend(scans(child))
    return found


def measure(conn, query: str, runs: int) -> tuple[float, list[str]]:
    explain = f"EXPLAIN (ANALYZE, FORMAT JSON) {query}"
    conn.execute(explain)  # warm-up
    times, plan = [], None
    for _ in range(runs):
        result = conn.execute(explain).fetchone()[0]
        result = json.loads(result) if isinstance(result, str) else result
        times.append(result[0]["Execution Time"])
        plan = result[0]["Plan"]
    return statistics.median(times), scans(plan)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--runs", type=int, default=25)
    parser.add_argument("--query-dir", type=Path, default=QUERY_DIR)
    args = parser.parse_args(argv)

    with PostgresSettings.from_env().connect(autocommit=True) as conn:
        conn.execute("ANALYZE")  # fresh planner statistics so plans reflect the current data
        print("| Query | Median (ms) | Table access |")
        print("|---|---|---|")
        for path in sorted(args.query_dir.glob("*.sql")):
            median, accesses = measure(conn, path.read_text(), args.runs)
            print(f"| {path.stem} | {median:.2f} | {'; '.join(accesses)} |")


if __name__ == "__main__":
    main()
