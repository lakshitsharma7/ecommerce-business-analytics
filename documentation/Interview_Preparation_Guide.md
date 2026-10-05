# Project Interview Notes

## A concise, accurate summary

> “I built an end-to-end analytics portfolio project using synthetic e-commerce data. A Python pipeline cleans four defect-injected CSVs, records its actions, and loads validated tables into SQLite. I wrote SQL for sales, customers, products, discounts, returns, inventory, and targets, then built a six-page local dashboard that queries the warehouse. I also prepared an Excel workbook that separates sample formula analysis from full-warehouse SQL results and documented the definitions and limitations. The existing PBIX is only a stub, so I do not present the browser dashboard as Power BI.”

## Questions to be ready for

### How did you define repeat customers?

As customers with at least two distinct order headers in `fact_orders`, divided by customers with at least one header. The current result is 7,891 / 7,986 = 98.81%. Because cancelled order headers are included, it is not a completed-purchase retention rate.

### What does line-item profit mean?

`net_sales - total_cost` in `fact_order_details`. It excludes recorded refunds and any operating, fulfillment, or return-handling expenses. Refund-adjusted profit subtracts recorded refunds only and is not operating profit or EBITDA.

### What did the cleaning pipeline do with missing customer keys?

It rejects those orders instead of assigning a fabricated guest ID. The audit records 820 rejected rows. Two of 822 raw missing-key rows overlap with duplicates.

### What is in the Power BI file?

The 1.7 KB PBIX is not a functional report. A DAX reference file and theme proposal exist, but neither has been validated in a Power BI model. The running dashboard is a separate browser prototype.

### What would you improve next?

Define completed/cancelled-order treatment, reconcile sales actuals to targets at matching period/region/category grain, and obtain operational costs and return-processing data before making causal or profitability recommendations.

## Reproducibility

Start with the run commands in the repository [README](../README.md). SQL and dashboard tests are included under `scripts/`.
