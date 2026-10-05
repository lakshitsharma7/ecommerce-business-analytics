# Data Cleaning and Transformation

## Pipeline

`scripts/clean_raw_datasets.py` reads the four defect-injected CSVs in `data/raw/`, writes cleaned CSVs to `data/cleaned/`, and records counts and actions in `data/cleaned/cleaning_audit.json`. The raw inputs are not modified. The SQLite loader consumes the cleaned tables and only replaces the warehouse after a successful build and validation.

Generated returns are preserved in `data/source/fact_returns_generated.csv`. The cleaning pipeline removes returns whose parent orders or order lines were rejected. Inventory and sales targets are generated as clean sources directly; they have no defect-injected raw counterparts.

## Audited row counts and actions

| Source | Raw rows | Clean rows | Removed/rejected | Recorded corrections |
| --- | ---: | ---: | ---: | --- |
| `raw_products_with_defects.csv` | 500 | 500 | 0 | 28 product names normalized; 10 negative selling-price signs fixed; 17 category labels normalized; 7 blank brands inferred |
| `raw_customers_with_defects.csv` | 8,080 | 8,000 | 80 duplicates | 253 missing ages filled using raw median 45; names, gender codes, and segments normalized |
| `raw_orders_with_defects.csv` | 52,150 | 51,180 | 150 duplicates and 820 missing-customer-key rows | 2,980 dates standardized; 1,507 order-status labels normalized |
| `raw_order_details_with_defects.csv` | 106,382 | 104,673 | 1,709 rows with rejected parent orders | 823 negative quantities corrected; 3,181 text-percent discounts normalized; 560 zero gross-sales values recalculated |
| Generated return source | 3,024 | 2,983 | 41 rows with rejected parent orders/lines | Filtered to retained order lines |

There are 822 raw order rows with missing customer keys. Two overlap with duplicate rows, so 820 are rejected in addition to 150 duplicate removals, for 970 total order rows removed.

## Transformation rules

- **Products:** trim/normalize product names and category labels; correct negative selling-price signs; infer blank brand values from product names where the pipeline rule applies.
- **Customers:** deduplicate by customer key; normalize strings and categorical codes; fill missing age values using the median of the raw age column (45).
- **Orders:** normalize supported date formats and status casing; remove duplicates; reject rows without a valid customer key rather than inventing a guest key.
- **Order details:** retain only rows whose parent orders survive cleaning; normalize percentage text; correct negative quantity signs; recalculate the identified zero gross-sales values.
- **Returns:** preserve generated source rows separately and remove those referencing rejected orders or lines.

The Excel cleaning sheet is an instructional formula sample, not the implementation of these production rules. It visibly notes where its examples differ from the Python pipeline.

## Rebuild

From the repository root:

```bash
python scripts/clean_raw_datasets.py
python scripts/load_sql_database.py
```

See the machine-readable [`cleaning_audit.json`](../data/cleaned/cleaning_audit.json) for per-source counts.
