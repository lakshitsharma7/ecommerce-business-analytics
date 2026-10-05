# Data assets

All project data is synthetic. The defect-injected source CSVs in `raw/` are kept unchanged by the cleaning pipeline. `source/fact_returns_generated.csv` preserves the generated returns before rows with rejected parent orders/lines are filtered. `cleaned/` contains the cleaned warehouse CSVs and the JSON transformation audit. `ecommerce_analytics.db` is the local SQLite warehouse.

## Rebuild the clean layer and warehouse

Run from the repository root:

```bash
python scripts/clean_raw_datasets.py
python scripts/load_sql_database.py
python scripts/test_sql_queries.py
```

The loader builds a temporary database, checks foreign keys, and replaces the prior warehouse only after successful completion.

## Regenerating synthetic source files

`python scripts/generate_synthetic_data.py` is optional and deterministic. It overwrites the existing generated raw CSVs and generated return source; do not run it just to rebuild the cleaned layer or SQLite database. Inventory and sales targets are generated directly as clean synthetic sources and have no corresponding defect-injected raw CSV.

The redundant ZIP bundle is excluded from Git; its contents duplicate the CSV and workbook assets.
