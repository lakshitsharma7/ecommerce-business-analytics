# Data Validation and Test Results

## Current warehouse checks

The SQLite warehouse contains 10 tables and three KPI views. Current table row counts:

| Table | Rows |
| --- | ---: |
| `dim_date` | 1,096 |
| `dim_region` | 4 |
| `dim_category` | 15 |
| `dim_product` | 500 |
| `dim_customer` | 8,000 |
| `fact_orders` | 51,180 |
| `fact_order_details` | 104,673 |
| `fact_returns` | 2,983 |
| `fact_inventory` | 18,000 |
| `fact_sales_targets` | 576 |

The order-date range is 2023-01-01 through 2025-12-31. The loader runs SQLite foreign-key checks before replacing the existing warehouse. `sql/07_data_validation.sql` verifies core warehouse conditions and defines the repeat-customer calculation explicitly.

## Automated execution

The current local validation run completed successfully:

- **32** statements in `sql/05_business_analysis.sql`
- **4** statements in `sql/07_data_validation.sql`
- **36** analysis and validation statements executed without SQL errors
- Dashboard measures and filter validation are exercised by `scripts/test_dashboard.py`
- Raw CSV checksums were the same before and after the cleaning run

Run the checks from the repository root:

```bash
python scripts/test_sql_queries.py
python -m unittest scripts.test_dashboard
```

## Measure definitions checked

- Repeat-customer rate: 7,891 customers with 2+ distinct order headers / 7,986 customers with at least one order header = **98.8104%**.
- One-time customers: **95** (exactly one distinct order header).
- Return-unit rate: 4,172 returned units / 188,832 units on order lines = **2.2094%**.
- Target attainment: $71,564,192.67 net sales / $34,910,032.51 sales targets = **204.9961%**.

Order-header counts include all statuses, including cancelled orders. The return-unit denominator also includes all order-line quantities; interpret these as warehouse definitions, not completed-sales rates.
