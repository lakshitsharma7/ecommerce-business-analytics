# Local dashboard prototype

This six-page HTML/CSS/JavaScript prototype reads from `data/ecommerce_analytics.db` through the read-only API in `server.py`. It is a browser application, not a Power BI report.

## Run

From the repository root:

```bash
python dashboard/server.py
```

Open `http://127.0.0.1:8000/`. The server binds to localhost and uses only the Python standard library.

## Pages and filters

Pages: Executive Overview, Sales Performance, Customer Analytics, Product Analytics, Inventory & Operations, and Returns & Profitability.

Filters: year, region, category, sales channel, and customer segment. Target facts have no channel or segment columns; inventory is a monthly product snapshot without region/channel/segment keys. The interface calls out these limitations.

Sales and line-item profit include all stored order statuses, including cancelled orders. Returns are shown separately; refund-adjusted profit subtracts recorded refunds only.

See `../screenshots/` for browser captures and `../powerbi/README.md` for the separate Power BI asset status.
