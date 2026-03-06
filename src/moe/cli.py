from __future__ import annotations

import argparse
import csv
from pathlib import Path

from moe.store import DuckDBStore


def _default_db_path() -> Path:
    return Path("data") / "moe.duckdb"


def _load_sample_rows(sample_dir: Path) -> list[dict[str, str]]:
    sample_file = sample_dir / "normalized_polls.csv"
    with sample_file.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [dict(row) for row in reader]


def cmd_init_db(args: argparse.Namespace) -> int:
    store = DuckDBStore(args.db)
    with store.session() as conn:
        store.initialize_schema(conn)
    print(f"Initialized schema in {args.db}")
    return 0


def cmd_fetch_data(args: argparse.Namespace) -> int:
    store = DuckDBStore(args.db)
    with store.session() as conn:
        if args.init_db:
            store.initialize_schema(conn)
            print(f"Initialized schema in {args.db}")

    print("fetch-data pipeline hook executed (no remote fetch configured in this repo)")
    return 0


def cmd_load_sample(args: argparse.Namespace) -> int:
    store = DuckDBStore(args.db)
    rows = _load_sample_rows(Path(args.sample_dir))

    for row in rows:
        if row.get("poll_id"):
            row["poll_id"] = int(row["poll_id"])
        if row.get("clean_poll_id"):
            row["clean_poll_id"] = int(row["clean_poll_id"])
        if row.get("sample_size"):
            row["sample_size"] = int(row["sample_size"])

    with store.session() as conn:
        store.initialize_schema(conn)
        inserted = store.write_rows_transactional(conn, "clean_normalized_polls", rows)

        print(f"Inserted {inserted} sample rows from {args.sample_dir}")
        if args.verify:
            records = store.readback(conn, "clean_normalized_polls", limit=args.limit)
            print(f"Read back {len(records)} rows from clean_normalized_polls")
            for record in records:
                print(record)
    return 0


def cmd_readback(args: argparse.Namespace) -> int:
    store = DuckDBStore(args.db)
    with store.session() as conn:
        rows = store.readback(conn, args.table, args.limit)

    print(f"Read back {len(rows)} rows from {args.table}")
    for row in rows:
        print(row)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="moe", description="MOE data storage CLI")
    parser.add_argument("--db", default=str(_default_db_path()), help="Path to DuckDB database")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_db = subparsers.add_parser("init-db", help="Initialize database schema")
    init_db.set_defaults(func=cmd_init_db)

    fetch_data = subparsers.add_parser("fetch-data", help="Fetch pipeline hook")
    fetch_data.add_argument("--init-db", action="store_true", help="Initialize schema before fetch")
    fetch_data.set_defaults(func=cmd_fetch_data)

    load_sample = subparsers.add_parser("load-sample", help="Load sample dataset from data_sample/")
    load_sample.add_argument("--sample-dir", default="data_sample", help="Directory containing normalized_polls.csv")
    load_sample.add_argument("--verify", action="store_true", help="Print readback rows after insert")
    load_sample.add_argument("--limit", type=int, default=5, help="Readback row limit when --verify is set")
    load_sample.set_defaults(func=cmd_load_sample)

    readback = subparsers.add_parser("readback", help="Read back rows from a table")
    readback.add_argument("--table", default="clean_normalized_polls", help="Table to query")
    readback.add_argument("--limit", type=int, default=5, help="Maximum rows to print")
    readback.set_defaults(func=cmd_readback)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
