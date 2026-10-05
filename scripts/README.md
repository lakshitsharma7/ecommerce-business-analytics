# Project scripts

Run these commands from the repository root.

| Script | Purpose |
| --- | --- |
| `generate_synthetic_data.py` | Optional deterministic generation of synthetic raw sources; overwrites generated CSVs |
| `clean_raw_datasets.py` | Preserve raw data, clean source CSVs, and write the JSON audit |
| `load_sql_database.py` | Safely build the SQLite warehouse from cleaned CSVs |
| `test_sql_queries.py` | Execute the analysis and validation SQL |
| `test_dashboard.py` | Test dashboard metric definitions, filters, and invalid values |
| `build_excel_workbook.py` | Build sample formula sheets plus current full-warehouse results |
| `build_executive_report.py` | Generate the PDF report from SQLite |
| `build_dashboard_gif.py` | Animate the six actual 1280×720 dashboard screenshots |
