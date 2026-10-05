# Excel workbook

`Ecommerce_Analytics.xlsx` contains formula demonstrations and full-warehouse results:

- `00_Read_Me` explains which sheets are samples and which are database-backed.
- `01_Raw_Data` uses up to 1,500 raw order lines; `02_Data_Cleaning` demonstrates formulas on a subset and is not the production cleaner.
- `03_Customers` contains the first 1,000 cleaned customers; `04_Products` contains the cleaned product catalog.
- `05_Orders` contains the first 2,000 cleaned order lines. `06_Pivot_Analysis` and `07_KPI_Summary` are formula examples based on that sample and do not introduce assumed business targets.
- `08_Business_Insights` and `09_Warehouse_KPIs` use SQL results from the full current SQLite warehouse.

Rebuild it from the repository root after cleaning and loading the database:

```bash
python scripts/build_excel_workbook.py
```

`openpyxl` writes formulas but does not calculate their cached values; Excel calculates those formula cells when the workbook is opened. The values on `09_Warehouse_KPIs` are static SQL results from build time and should be refreshed by rebuilding the workbook after changing the warehouse.
