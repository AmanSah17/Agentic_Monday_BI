from __future__ import annotations

from typing import Any

import duckdb
import pandas as pd


class DuckDBSession:
    def __init__(self) -> None:
        self._conn = duckdb.connect(database=":memory:")

    def register_tables(self, tables: dict[str, pd.DataFrame]) -> None:
        for table_name, df in tables.items():
            self._conn.register(table_name, df)

    def query(self, sql: str) -> pd.DataFrame:
        return self._conn.execute(sql).df()

    def describe_schema(self, table_names: list[str]) -> dict[str, list[dict[str, Any]]]:
        schema: dict[str, list[dict[str, Any]]] = {}
        for table_name in table_names:
            info_df = self._conn.execute(f"DESCRIBE SELECT * FROM {table_name}").df()
            schema[table_name] = info_df.to_dict(orient="records")
        return schema

