# Executive Report

| Project | E-Commerce Sales, Customer & Business Performance Analytics |
| --- | --- |
| Company | ApexCart Retail Inc. (synthetic) |
| Period | 2023-01-01 to 2025-12-31 |

## Executive summary

The current synthetic warehouse contains 51,180 order headers and 104,673 order lines across a 3-year date range. Stored order-line net sales are **$71.56M** and line-item profit is **$18.53M** (a **25.90%** margin before refunds and operating expenses). The warehouse also contains 2,983 return incidents, 18,000 product/month inventory snapshots, and 576 monthly region/category target rows.

The strongest descriptive patterns are a large sales contribution from Technology, lower observed margins in the highest discount band, recorded refunds of $1.55M, and 64 products at or below their latest reorder levels. These are investigation signals, not causal or financial forecasts.

## Performance summary

| Measure | Current result |
| --- | ---: |
| Gross sales | $77,161,511.63 |
| Discounts | $5,597,318.96 |
| Net sales | $71,564,192.67 |
| COGS | $53,032,485.66 |
| Line-item profit | $18,531,707.01 |
| Line-item margin | 25.90% |
| Distinct orders | 51,180 |
| Average order value | $1,398.28 |
| Recorded refunds | $1,545,024.47 |
| Refund-adjusted profit | $16,986,682.54 |
| Aggregate sales-target attainment | 205.00% |

## Findings for review

### Product and discount mix

Technology accounts for **$41.03M (57.3%)** of net sales, with a **22.9%** line-item margin. Furniture contributes **$26.16M** at **29.3%**. The `>20%` discount band has a **6.5%** observed line margin, compared with **31.3%** for lines with no discount. Product and channel mix are not controlled; this should not be described as causal discount elasticity.

### Customers

Of 7,986 customers with an order header, 7,891 have at least two distinct order headers and 95 have one. The 98.81% repeat-header rate includes cancelled order headers. Recalculate with completed orders and a defined time window before interpreting it as retention.

### Returns

The warehouse records **2,983** return incidents, **4,172** returned units, and **$1.545M** in refunds. Returned units are **2.21%** of all units on order lines. `Damaged in Transit` is the most frequent recorded reason (521 incidents); `Size / Fit Mismatch` has the largest aggregate refund amount ($286,499.46). Reverse freight and handling costs are not modeled.

### Inventory and targets

The latest inventory snapshot, **2025-12-01**, has 132,045 closing units valued at **$37.28M** using product cost; 64 SKUs are at or below reorder levels. Summed sales targets are **$34.91M** and stored net sales are **$71.56M**. The ratio is 205.00%, but sales include cancelled statuses; target actuals should be reconciled by period, region, and category before management use.

## Scope and limitations

- All inputs are synthetic and deterministic; these findings do not describe a real company or customers.
- Current sales and line-item profit calculations include all order statuses, including cancelled orders.
- Line-item profit is net sales less COGS. Refund-adjusted profit subtracts recorded refunds only and is not operating profit or EBITDA.
- The dataset has no marketing spend/CAC, operating expense, return freight, or controlled experiment fields.
- Targets have no channel or customer-segment dimensions. Inventory is a monthly product snapshot with no region/channel/segment dimensions.
- The browser dashboard is not a Power BI report; the PBIX stub and DAX reference are not validated deliverables.

## Recommended next analysis steps

1. Agree on completed-order and cancellation treatment for financial measures.
2. Compare targets and actuals at the same period, region, and category grain.
3. Test discount patterns within comparable product/channel groups before proposing pricing changes.
4. Add completed-purchase customer cohorts and operational return costs for retention and return economics.
5. Enrich inventory with lead times and stockout/out-of-stock history before estimating lost sales.
