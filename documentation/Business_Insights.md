# Business Insights from the Current Synthetic Warehouse

These results are calculated from the current `data/ecommerce_analytics.db`. They are descriptive, not forecasts or causal conclusions.

## Financial and customer measures

- Gross sales are **$77,161,511.63**, with **$5,597,318.96** in stored discounts and **$71,564,192.67** in net sales.
- Stored line-item COGS is **$53,032,485.66**; line-item profit is **$18,531,707.01**, or **25.90%** of net sales. This excludes refunds and operating expenses.
- The 7,986 customers with at least one order header include **7,891** with two or more distinct order headers and **95** with one. The resulting repeat-header rate is **98.81%**. All order statuses, including cancelled, are included, so this is not a completed-order retention measure.

## Product and discount patterns

- Technology contributes **$41,025,397.18** in net sales (**57.3%** of the total) at a **22.9%** line-item margin.
- Furniture contributes **$26,162,811.11** at a **29.3%** margin. Office Supplies and Apparel & Gear have higher observed line-item margins (**33.3%** and **33.8%**) on lower sales totals.
- Lines in the `>20%` discount band have a **6.5%** margin compared with **31.3%** for the `0%` band. These tiers differ in product and channel mix; the comparison does not establish that discounts caused the margin difference or estimate incremental sales.

## Region, returns, and inventory

- North America has the highest net sales at **$29,702,500.47**. Observed regional line margins are close, ranging from approximately **25.8% to 26.1%**.
- The warehouse records **2,983** return incidents, **4,172** returned units, and **$1,545,024.47** in refunds. Returned units are **2.21%** of units on all order lines. `Damaged in Transit` is the most frequent reason (521 incidents); `Size / Fit Mismatch` has the largest total refund amount (**$286,499.46**).
- The latest inventory snapshot is **2025-12-01**: **132,045** closing units valued at **$37,282,641.98** using product cost. **64** SKUs are at or below their reorder levels.

## Targets and follow-up

Summed sales targets are **$34,910,032.51**; net sales divided by this sum is **205.00%**. The actual sales measure includes cancelled order lines, and targets do not include channel or customer-segment fields. Validate status and target scope before using this as a performance result.

Reasonable next steps for a richer analysis would be to define completed orders, align actuals to target periods, compare discount groups within like-for-like products, and join inventory to replenishment lead times. Those questions cannot be answered fully from the current synthetic fields.
