"""Build the SQLite warehouse atomically from the cleaned CSV tables."""

import csv
import os
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "ecommerce_analytics.db"
CLEANED_DIR = ROOT / "data" / "cleaned"
DDL_PATH = ROOT / "sql" / "02_create_tables.sql"
TEMP_DB_PATH = DB_PATH.with_name("ecommerce_analytics.build.db")

TABLES_TO_LOAD = [
    ("dim_region", "dim_region.csv"),
    ("dim_category", "dim_category.csv"),
    ("dim_date", "dim_date.csv"),
    ("dim_product", "dim_product.csv"),
    ("dim_customer", "dim_customer.csv"),
    ("fact_orders", "fact_orders.csv"),
    ("fact_order_details", "fact_order_details.csv"),
    ("fact_returns", "fact_returns.csv"),
    ("fact_inventory", "fact_inventory.csv"),
    ("fact_sales_targets", "fact_sales_targets.csv"),
]


def build_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if TEMP_DB_PATH.exists():
        TEMP_DB_PATH.unlink()

    connection = sqlite3.connect(TEMP_DB_PATH)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(DDL_PATH.read_text(encoding="utf-8"))
        for table_name, csv_name in TABLES_TO_LOAD:
            csv_path = CLEANED_DIR / csv_name
            with csv_path.open(encoding="utf-8-sig", newline="") as handle:
                reader = csv.DictReader(handle)
                if reader.fieldnames is None:
                    raise ValueError(f"CSV has no header: {csv_path}")
                columns = reader.fieldnames
                placeholders = ",".join("?" for _ in columns)
                quoted_columns = ",".join(
                    '"' + column.replace('"', '""') + '"' for column in columns
                )
                sql = (
                    f'INSERT INTO "{table_name}" '
                    f"({quoted_columns}) "
                    f"VALUES ({placeholders})"
                )
                rows = []
                for row in reader:
                    values = [row[column] for column in columns]
                    if table_name == "dim_customer":
                        values[columns.index("age")] = (
                            values[columns.index("age")] or None
                        )
                    rows.append(values)
                connection.executemany(sql, rows)
            print(f"Loaded {len(rows):,} rows into {table_name}")

        violations = connection.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(f"Foreign-key violations found: {violations[:5]}")
        connection.commit()
    except Exception:
        connection.rollback()
        connection.close()
        if TEMP_DB_PATH.exists():
            TEMP_DB_PATH.unlink()
        raise
    else:
        connection.close()

    os.replace(TEMP_DB_PATH, DB_PATH)
    print(f"Database verified and replaced atomically: {DB_PATH}")


if __name__ == "__main__":
    build_database()
