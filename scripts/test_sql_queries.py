"""Execute the project SQL analysis, KPI views, and validation queries."""

import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "ecommerce_analytics.db"
SQL_FILES = [
    ROOT / "sql" / "06_kpi_queries.sql",
    ROOT / "sql" / "05_business_analysis.sql",
    ROOT / "sql" / "07_data_validation.sql",
]


def statements_from(path: Path) -> list[str]:
    contents = "\n".join(
        line for line in path.read_text(encoding="utf-8").splitlines()
        if not line.strip().startswith("--")
    )
    statements = []
    for block in contents.split(";"):
        statement = block.strip()
        if statement:
            statements.append(statement)
    return statements


def run() -> int:
    if not DB_PATH.is_file():
        raise FileNotFoundError(
            f"Database not found at {DB_PATH}; run scripts/load_sql_database.py"
        )
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SQL_FILES[0].read_text(encoding="utf-8"))
        count = 0
        for path in SQL_FILES[1:]:
            for index, statement in enumerate(statements_from(path), start=1):
                try:
                    cursor = connection.execute(statement)
                    if cursor.description:
                        cursor.fetchall()
                except sqlite3.Error as error:
                    raise RuntimeError(
                        f"{path.relative_to(ROOT)} statement {index} failed: {error}\n"
                        f"{statement[:500]}"
                    ) from error
                count += 1
                print(f"[OK] {path.name} statement {index}")
    print(f"All {count} analysis and validation statements executed successfully.")
    return count


if __name__ == "__main__":
    run()
