# Business Requirements and Scope

## Project

**E-Commerce Sales, Customer & Business Performance Analytics**

Synthetic company: **ApexCart Retail Inc.**

## Business context

ApexCart is a synthetic retailer whose example data covers order headers and lines, customers, products, returns, monthly inventory snapshots, and sales targets. The project provides a consistent way to examine sales, line-item profit, discount patterns, repeat order frequency, returns, inventory levels, and target comparisons.

The data is artificial and should not be treated as evidence about an actual retailer or actual customers.

## Questions the analysis addresses

- What are gross sales, discounts, net sales, COGS, and line-item profit?
- How do these amounts vary by time, region, product, category, channel, and customer segment?
- What proportion of customers represented in order headers have one versus multiple order headers?
- Which product and discount groups have different observed line-item margins?
- How many returns, returned units, and refunds are recorded, and what reasons are supplied?
- What do the latest inventory snapshots show relative to product reorder levels?
- How do net sales compare with stored monthly regional/category sales targets?

## Stakeholders and outputs

| Audience | Analytical need | Repository output |
| --- | --- | --- |
| Executive reader | Summary of the measures, results, and caveats | README, executive report, dashboard overview |
| Sales/finance analyst | Sales, profit, target, region, and channel comparisons | SQL analyses, KPI views, dashboard |
| Customer analyst | Order-frequency and segment comparisons | SQL analyses, dashboard |
| Product/operations analyst | Product economics, returns, and inventory alerts | SQL analyses, dashboard |
| Recruiter/reviewer | Reproducible, transparent demonstration of analysis work | Source scripts, data dictionary, screenshots, tests |

## Definitions and guardrails

- **Net sales:** stored line gross sales minus stored line discounts.
- **Line-item profit:** stored line net sales minus stored line COGS. It does not subtract refunds or operating expenses.
- **Refund-adjusted profit:** line-item profit less recorded refund amounts. This is not operating profit or EBITDA.
- **Repeat customer:** a customer with at least two distinct order headers in `fact_orders`; all order statuses are included.
- **Return-unit rate:** returned units divided by units on order lines. It is not a return rate by distinct order.
- **Target attainment:** net sales divided by the summed target for the compared scope. Targets are by month, region, and category, not by channel or customer segment.

## Delivered scope

- Deterministic synthetic data generation and documented defect injection
- Raw-to-clean transformations with a JSON audit and preserved raw inputs
- SQLite relational warehouse, constraints, indexes, KPI views, and validation queries
- 32 SQL business analyses, focused dashboard tests, and SQL execution tests
- Excel workbook with illustrative sample formulas and separate full-warehouse values
- Six-page, read-only local browser dashboard
- Executive report in Markdown and PDF

## Explicitly not delivered

- A usable Power BI PBIX/model or validated DAX measures
- Real customer or retailer data
- Causal experiments, discount elasticity estimates, churn models, or financial forecasts
- Operating expenses, acquisition costs, reverse-freight costs, or complete return-handling costs
- A GitHub remote or upload; repository preparation remains local until separately requested
