from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping

import duckdb


class DuckDBStore:
    """Thin helper around DuckDB connections for MOE ingestion workflows."""

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def connect(self) -> duckdb.DuckDBPyConnection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        return duckdb.connect(str(self.db_path))

    @contextmanager
    def session(self) -> Iterator[duckdb.DuckDBPyConnection]:
        conn = self.connect()
        try:
            yield conn
        finally:
            conn.close()

    @contextmanager
    def transaction(self, conn: duckdb.DuckDBPyConnection) -> Iterator[duckdb.DuckDBPyConnection]:
        conn.execute("BEGIN TRANSACTION")
        try:
            yield conn
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise

    def initialize_schema(self, conn: duckdb.DuckDBPyConnection, schema_path: str | Path | None = None) -> None:
        schema_file = Path(schema_path) if schema_path else Path(__file__).with_name("schema.sql")
        conn.execute(schema_file.read_text(encoding="utf-8"))

    def insert_rows(
        self,
        conn: duckdb.DuckDBPyConnection,
        table: str,
        rows: Iterable[Mapping[str, Any]],
    ) -> int:
        rows = list(rows)
        if not rows:
            return 0

        columns = list(rows[0].keys())
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({placeholders})"
        values = [tuple(row[column] for column in columns) for row in rows]
        conn.executemany(sql, values)
        return len(values)

    def write_rows_transactional(
        self,
        conn: duckdb.DuckDBPyConnection,
        table: str,
        rows: Iterable[Mapping[str, Any]],
    ) -> int:
        with self.transaction(conn):
            return self.insert_rows(conn, table, rows)

    def readback(self, conn: duckdb.DuckDBPyConnection, table: str, limit: int = 5) -> list[tuple[Any, ...]]:
        return conn.execute(f"SELECT * FROM {table} LIMIT ?", [limit]).fetchall()
