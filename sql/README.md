# SQL assets

| File | Purpose |
| --- | --- |
| `01_create_database.sql` | SQLite database setup notes and pragmas |
| `02_create_tables.sql` | Dimension/fact DDL, constraints, foreign keys, and indexes |
| `03_insert_data.sql` | CSV import/warehouse load reference |
| `04_data_quality_checks.sql` | SQL data-quality checks |
| `05_business_analysis.sql` | 32 business-analysis queries |
| `06_kpi_queries.sql` | Three KPI view definitions |
| `07_data_validation.sql` | Warehouse validation and repeat-customer definition |

The project runner uses `06_kpi_queries.sql`, executes all 32 business queries and all four validation queries, and raises an error if a statement fails:

```bash
python scripts/test_sql_queries.py
```

See [SQL_Analysis.md](../documentation/SQL_Analysis.md) for query domains, techniques, and interpretation caveats.
