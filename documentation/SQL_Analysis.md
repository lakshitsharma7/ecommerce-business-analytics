# SQL Business Analysis Guide

`sql/05_business_analysis.sql` contains 32 SQLite-compatible business questions. The companion KPI-view definitions are in `sql/06_kpi_queries.sql`; data checks and the repeat-customer definition are in `sql/07_data_validation.sql`.

## Query domains

| Queries | Domain | Questions covered |
| --- | --- | --- |
| Q1–Q6 | Revenue and growth | Monthly and annual revenue/profit, month-over-month and year-over-year change, cumulative pacing, moving averages, day-of-week patterns |
| Q7–Q13 | Customers | One-time versus repeat order headers, new/returning order activity, RFM scoring, spend deciles, top customers, demographics, time to second order |
| Q14–Q20 | Products and pricing | Product rankings, low-profit products, Pareto concentration, product margin matrix, category/sub-category results, discount bands and line-level margin |
| Q21–Q25 | Region, channel, and targets | Monthly target variance, regional ranking, channel margin, payment methods, shipping modes |
| Q26–Q32 | Returns and operations | Category return rates/refunds, reason and product diagnostics, inventory turnover, reorder alerts, cancellations, financial bridge |

The project SQL execution runner successfully executed all 32 statements against the rebuilt warehouse.

## Techniques actually present

- Joins and grouped aggregate calculations
- Conditional `CASE` expressions and subqueries
- Common table expressions (`WITH`)
- Window functions: `LAG`, `ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`, and windowed `SUM`/`AVG`
- `NULLIF` for safe ratio calculations
- KPI views for monthly executive KPIs, regional target achievement, and RFM segments

## Important interpretation notes

- Query results use the stored order lines and the SQL in the repository; order status is not generally excluded from revenue/profit sums. Cancelled orders therefore remain in measures unless an individual query explicitly filters status.
- `fact_order_details.net_profit` is line-item profit before returns and operating expenses.
- The target table is month/region/category. Channel and customer-segment target comparisons are not available.
- Return rates depend on their denominator. The dashboard's overall unit rate is returned units divided by all order-line units.
- RFM labels and discount bands are descriptive groupings over synthetic data, not validated customer lifecycle or causal pricing models.

See the SQL comments for each query's exact business question and calculation.
