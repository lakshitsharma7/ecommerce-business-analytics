const pageTitles = {
  executive: "Executive Overview",
  sales: "Sales Performance",
  customers: "Customer Analytics",
  products: "Product Analytics",
  inventory: "Inventory & Operations",
  returns: "Returns & Profitability",
};
const colors = ["series-a", "series-b", "series-c", "series-a", "series-b"];
const money = (value) => {
  const amount = Number(value || 0);
  if (Math.abs(amount) >= 1e6) return `$${(amount / 1e6).toFixed(2)}M`;
  if (Math.abs(amount) >= 1e3) return `$${(amount / 1e3).toFixed(1)}K`;
  return `$${amount.toFixed(0)}`;
};
const fullMoney = (value) => new Intl.NumberFormat("en-US", {
  style: "currency", currency: "USD", maximumFractionDigits: 0,
}).format(Number(value || 0));
const integer = (value) => new Intl.NumberFormat("en-US", {
  maximumFractionDigits: 0,
}).format(Number(value || 0));
const percent = (value, digits = 1) => `${Number(value || 0).toFixed(digits)}%`;
const escapeHtml = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);
let currentPage = "executive";
let latestData = null;
let pendingRequest = 0;

function chartCard(title, body, note = "") {
  return `<article class="card"><div class="card-head"><h2 class="card-title">${escapeHtml(title)}</h2><span class="card-note">${escapeHtml(note)}</span></div><div class="card-body">${body}</div></article>`;
}

function emptyState(message) {
  return `<div class="empty">${escapeHtml(message)}</div>`;
}

function barChart(rows, labelKey, valueKey, format = money, color = "series-a") {
  if (!rows?.length) return emptyState("No rows match the selected filters.");
  const width = 640, height = 184, left = 48, right = 12, top = 10, bottom = 32;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const max = Math.max(...rows.map((item) => Number(item[valueKey] || 0)), 1);
  const step = plotWidth / rows.length;
  const barWidth = Math.max(5, Math.min(34, step * 0.62));
  const bars = rows.map((item, index) => {
    const value = Number(item[valueKey] || 0);
    const barHeight = Math.max(value > 0 ? 2 : 0, value / max * plotHeight);
    const x = left + step * index + (step - barWidth) / 2;
    const y = top + plotHeight - barHeight;
    const label = String(item[labelKey] ?? "");
    const axisLabel = label.length > 13 ? `${label.slice(0, 12)}…` : label;
    return `<rect class="${color}" x="${x.toFixed(1)}" y="${y.toFixed(1)}" width="${barWidth.toFixed(1)}" height="${barHeight.toFixed(1)}" rx="3"><title>${escapeHtml(label)}: ${escapeHtml(format(value))}</title></rect><text x="${(x + barWidth / 2).toFixed(1)}" y="${height - 10}" text-anchor="middle">${escapeHtml(axisLabel)}</text>`;
  }).join("");
  const grid = [0, 0.5, 1].map((fraction) => {
    const y = top + plotHeight * fraction;
    return `<line class="grid-line" x1="${left}" x2="${width - right}" y1="${y}" y2="${y}"/><text x="${left - 7}" y="${y + 3}" text-anchor="end">${escapeHtml(format(max * (1 - fraction)))}</text>`;
  }).join("");
  return `<svg class="chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Bar chart">${grid}<line class="axis-line" x1="${left}" x2="${left}" y1="${top}" y2="${top + plotHeight}"/><line class="axis-line" x1="${left}" x2="${width - right}" y1="${top + plotHeight}" y2="${top + plotHeight}"/>${bars}</svg>`;
}

function monthlyChart(rows) {
  if (!rows?.length) return emptyState("No monthly data for the selected filters.");
  const width = 700, height = 184, left = 56, right = 15, top = 12, bottom = 30;
  const plotWidth = width - left - right, plotHeight = height - top - bottom;
  const max = Math.max(...rows.map((row) => Number(row.net_sales || 0)), 1);
  const step = plotWidth / rows.length;
  const barWidth = Math.max(3, Math.min(13, step * 0.65));
  const points = [];
  const bars = rows.map((row, index) => {
    const revenue = Number(row.net_sales || 0);
    const profit = Number(row.line_profit || 0);
    const x = left + step * index + (step - barWidth) / 2;
    const h = Math.max(revenue > 0 ? 1 : 0, revenue / max * plotHeight);
    const py = top + plotHeight - Math.max(0, profit) / max * plotHeight;
    points.push(`${(x + barWidth / 2).toFixed(1)},${py.toFixed(1)}`);
    const month = String(row.period).slice(5);
    const showLabel = index % Math.max(1, Math.ceil(rows.length / 12)) === 0;
    return `<rect class="series-a" x="${x.toFixed(1)}" y="${(top + plotHeight - h).toFixed(1)}" width="${barWidth.toFixed(1)}" height="${h.toFixed(1)}" rx="2"><title>${escapeHtml(row.period)} net sales: ${escapeHtml(money(revenue))}</title></rect>${showLabel ? `<text x="${(x + barWidth / 2).toFixed(1)}" y="${height - 9}" text-anchor="middle">${escapeHtml(month)}</text>` : ""}`;
  }).join("");
  const grid = [0, .5, 1].map((fraction) => {
    const y = top + plotHeight * fraction;
    return `<line class="grid-line" x1="${left}" x2="${width - right}" y1="${y}" y2="${y}"/><text x="${left - 7}" y="${y + 3}" text-anchor="end">${escapeHtml(money(max * (1 - fraction)))}</text>`;
  }).join("");
  const profitLine = points.length > 1 ? `<polyline class="line-a" points="${points.join(" ")}"/>` : "";
  const dots = points.map((point) => {
    const [x, y] = point.split(",");
    return `<circle class="dot-a" cx="${x}" cy="${y}" r="3"/>`;
  }).join("");
  return `<div class="legend"><span><i></i>Net sales</span><span><i class="profit-dot"></i>Line-item profit</span></div><svg class="chart" viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="Monthly net sales bars and line-item profit line">${grid}<line class="axis-line" x1="${left}" x2="${width - right}" y1="${top + plotHeight}" y2="${top + plotHeight}"/>${bars}${profitLine}${dots}</svg>`;
}

function barList(rows, labelKey, valueKey, formatter = money) {
  if (!rows?.length) return emptyState("No rows match the selected filters.");
  const maximum = Math.max(...rows.map((item) => Number(item[valueKey] || 0)), 1);
  return `<div class="bar-list">${rows.map((item, index) => {
    const value = Number(item[valueKey] || 0);
    const width = Math.min(100, Math.max(value > 0 ? 1 : 0, value / maximum * 100));
    return `<div class="bar-item"><div class="bar-label"><span title="${escapeHtml(item[labelKey])}">${escapeHtml(item[labelKey])}</span><span>${escapeHtml(formatter(value))}</span></div><div class="bar-track"><div class="bar-fill ${colors[index % colors.length]}" style="width:${width.toFixed(2)}%"></div></div></div>`;
  }).join("")}</div>`;
}

function dataTable(columns, rows) {
  if (!rows?.length) return emptyState("No rows match the selected filters.");
  return `<div class="table-wrap"><table><thead><tr>${columns.map((col) => `<th class="${col.numeric ? "numeric" : ""}">${escapeHtml(col.label)}</th>`).join("")}</tr></thead><tbody>${rows.map((row) => `<tr>${columns.map((col) => `<td class="${col.numeric ? "numeric" : ""}" title="${escapeHtml(col.format ? col.format(row[col.key]) : row[col.key])}">${escapeHtml(col.format ? col.format(row[col.key]) : row[col.key])}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`;
}

function renderKpis(data) {
  const m = data.metrics, inventory = data.inventory, target = data.targets;
  const sets = {
    executive: [
      ["Net sales", money(m.net_sales), "After line-item discounts"],
      ["Line-item profit", money(m.line_profit), `${percent(m.profit_margin_pct)} margin before refunds`],
      ["Orders", integer(m.orders), `${integer(m.units)} units on order lines`],
      ["Average order value", fullMoney(m.average_order_value), "Net sales / distinct orders"],
      ["Sales target attainment", target.sales_achievement_pct == null ? "n/a" : percent(target.sales_achievement_pct), "Target facts are not channel/segment sliced"],
    ],
    sales: [
      ["Gross sales", money(m.gross_sales), "Before discounts"],
      ["Discounts", money(m.discounts), `${percent(m.average_discount_pct)} of gross sales`],
      ["Net sales", money(m.net_sales), "After discounts"],
      ["Orders", integer(m.orders), "Distinct order headers"],
      ["Average order value", fullMoney(m.average_order_value), "Net sales / distinct orders"],
    ],
    customers: [
      ["Customers with orders", integer(m.customers_with_orders), "Current filter context"],
      ["Repeat customers", integer(m.repeat_customers), "At least 2 distinct orders"],
      ["Repeat-customer rate", percent(m.repeat_customer_rate_pct, 2), "Repeat / customers with orders"],
      ["One-time customers", integer(m.one_time_customers), "Exactly 1 distinct order"],
      ["One-time rate", percent(m.one_time_customer_rate_pct, 2), "One-time / customers with orders"],
    ],
    products: [
      ["Catalog products", integer(m.products), "Products represented in filtered sales"],
      ["Net sales", money(m.net_sales), "Across filtered product lines"],
      ["Line-item profit", money(m.line_profit), "Net sales less COGS"],
      ["Weighted margin", percent(m.profit_margin_pct), "Profit / net sales"],
      ["Average discount", percent(m.average_discount_pct), "Discounts / gross sales"],
    ],
    inventory: [
      ["Snapshot units", integer(inventory.units), "At selected/latest snapshot"],
      ["Inventory value", money(inventory.inventory_value), "Closing units × product cost"],
      ["Below reorder", integer(inventory.below_reorder_skus), "Distinct SKUs at/below threshold"],
      ["Snapshot date", inventory.snapshot_date || "n/a", "Last snapshot in selected year"],
      ["Year-to-date sales", money(m.net_sales), "Sales filters apply; inventory has no region/channel"],
    ],
    returns: [
      ["Return incidents", integer(m.return_incidents), "Distinct return IDs"],
      ["Refunds", money(m.refunds), "Recorded refund amount"],
      ["Units returned", integer(m.returned_units), `${percent(m.return_rate_pct, 2)} of sold units`],
      ["Refund-adjusted profit", money(m.refund_adjusted_profit), "Line-item profit less refunds"],
      ["Adjusted margin", percent(m.refund_adjusted_margin_pct), "Refund-adjusted profit / net sales"],
    ],
  };
  document.querySelector("#kpis").innerHTML = sets[currentPage].map(([label, value, note]) =>
    `<article class="kpi"><span class="kpi-label">${escapeHtml(label)}</span><strong class="kpi-value" title="${escapeHtml(value)}">${escapeHtml(value)}</strong><span class="kpi-note">${escapeHtml(note)}</span></article>`
  ).join("");
}

function renderTargetTable(data) {
  const target = data.targets;
  const rows = [{
    label: "Filtered target scope",
    target: target.sales_target,
    actual: target.actual_net_sales,
    achievement: target.sales_achievement_pct,
  }];
  return `<div class="target-table">${dataTable([
    { key: "label", label: "Scope" },
    { key: "target", label: "Sales target", numeric: true, format: fullMoney },
    { key: "actual", label: "Actual net sales", numeric: true, format: fullMoney },
    { key: "achievement", label: "Attainment", numeric: true, format: (v) => v == null ? "n/a" : percent(v) },
  ], rows)}<p class="data-note">${escapeHtml(data.metadata.targets_filters)}</p></div>`;
}

function renderProductTable(rows) {
  return dataTable([
    { key: "name", label: "Product" },
    { key: "category", label: "Category" },
    { key: "net_sales", label: "Net sales", numeric: true, format: money },
    { key: "line_profit", label: "Profit", numeric: true, format: money },
  ], rows);
}

function renderInventoryAlerts(rows) {
  return dataTable([
    { key: "name", label: "SKU / product" },
    { key: "category", label: "Category" },
    { key: "stock", label: "Closing stock", numeric: true, format: integer },
    { key: "reorder_level", label: "Reorder level", numeric: true, format: integer },
  ], rows);
}

function renderReturns(data) {
  const reasons = data.returns_by_reason.map((item) => ({
    name: item.name, incidents: item.incidents, refunds: item.refunds,
  }));
  const m = data.metrics;
  const bridge = [
    { name: "Gross sales", value: m.gross_sales },
    { name: "Net sales", value: m.net_sales },
    { name: "COGS", value: m.cogs },
    { name: "Line-item profit", value: m.line_profit },
    { name: "Refunds", value: m.refunds },
    { name: "Refund-adjusted profit", value: m.refund_adjusted_profit },
  ];
  return [chartCard("Return reason mix", dataTable([
    { key: "name", label: "Reason" },
    { key: "incidents", label: "Incidents", numeric: true, format: integer },
    { key: "refunds", label: "Refunds", numeric: true, format: money },
  ], reasons), "Refunds by recorded reason"),
  chartCard("Financial bridge", barList(bridge, "name", "value"), "Refund-adjusted profit is shown separately")];
}

function renderPage(data) {
  const targetNote = "Actuals and quota use year/region/category only.";
  const categoryNote = "Category filters apply to product-linked views.";
  const pages = {
    executive: [
      [chartCard("Monthly net sales and line-item profit", monthlyChart(data.monthly), "Monthly totals · order-date cohort"),
       chartCard("Net sales by region", barList(data.regions, "name", "net_sales"), "Selected filters")],
      [chartCard("Top products by net sales", renderProductTable(data.products), "Top 8 in current filter context"),
       chartCard("Sales target attainment", renderTargetTable(data), targetNote)],
    ],
    sales: [
      [chartCard("Monthly sales and profit trend", monthlyChart(data.monthly), "Order-date cohort"),
       chartCard("Sales by channel", barList(data.channels, "name", "net_sales"), "Channel sales · net")],
      [chartCard("Category performance", dataTable([
        { key: "name", label: "Category" },
        { key: "net_sales", label: "Net sales", numeric: true, format: money },
        { key: "line_profit", label: "Line profit", numeric: true, format: money },
      ], data.categories), categoryNote),
       chartCard("Sales target attainment", renderTargetTable(data), targetNote)],
    ],
    customers: [
      [chartCard("Net sales by customer segment", barList(data.segments, "name", "net_sales"), "Synthetic customer segments"),
       chartCard("Customers by segment", dataTable([
         { key: "name", label: "Segment" },
         { key: "customers", label: "Customers", numeric: true, format: integer },
         { key: "orders", label: "Orders", numeric: true, format: integer },
       ], data.segments), "Customer counts are distinct within the selected scope")],
      [chartCard("Repeat purchase definition", `<div class="bar-list"><div class="bar-item"><div class="bar-label"><span>Customers with 2+ distinct orders</span><span>${integer(data.metrics.repeat_customers)}</span></div><div class="bar-track"><div class="bar-fill green" style="width:${data.metrics.repeat_customer_rate_pct.toFixed(2)}%"></div></div></div><div class="bar-item"><div class="bar-label"><span>Customers with exactly 1 distinct order</span><span>${integer(data.metrics.one_time_customers)}</span></div><div class="bar-track"><div class="bar-fill amber" style="width:${data.metrics.one_time_customer_rate_pct.toFixed(2)}%"></div></div></div><p class="data-note">Rate = repeat customers / customers with at least one order. Customers with no orders are excluded.</p></div>`, "Exact order-frequency groups"),
       chartCard("Sales by region", barList(data.regions, "name", "net_sales"), "Selected customer/order scope")],
    ],
    products: [
      [chartCard("Top products by net sales", renderProductTable(data.products), "Product lines from the filtered warehouse"),
       chartCard("Weighted margin by category", barList(data.categories, "name", "margin_pct", (v) => percent(v)), "Line-item profit / net sales")],
      [chartCard("Discount tier economics", dataTable([
        { key: "name", label: "Discount tier" },
        { key: "units", label: "Units", numeric: true, format: integer },
        { key: "net_sales", label: "Net sales", numeric: true, format: money },
        { key: "line_profit", label: "Line profit", numeric: true, format: money },
      ], data.discounts), "Grouped by actual line discount rates"),
       chartCard("Products by net sales", barChart(data.products.slice(0, 6), "name", "net_sales"), "Top six · current filters")],
    ],
    inventory: [
      [chartCard("Inventory value by category", barList(data.inventory.by_category, "name", "inventory_value"), `Closing-stock cost value · ${data.inventory.snapshot_date || "no snapshot"}`),
       chartCard("Below-reorder products", renderInventoryAlerts(data.inventory.alerts), "Snapshot stock at/below product reorder level")],
      [chartCard("Closing units by category", barChart(data.inventory.by_category, "name", "units", integer, "series-b"), "Single selected/latest monthly snapshot"),
       chartCard("Inventory methodology", `<div class="empty">${escapeHtml(data.metadata.inventory_filters)}<br><br>Inventory is a monthly snapshot, not a transaction flow. The value is closing units multiplied by product cost.</div>`, "Interpret snapshots separately from sales")],
    ],
    returns: [renderReturns(data)],
  };
  const rows = pages[currentPage];
  document.querySelector("#dashboard-content").innerHTML = rows.map((row) =>
    `<div class="dashboard-row ${currentPage === "returns" ? "equal" : ""}">${row.join("")}</div>`
  ).join("");
}

function populateOptions(options) {
  const placeholders = {
    year: "All years", region: "All regions", category: "All categories",
    channel: "All channels", segment: "All segments",
  };
  for (const [key, values] of Object.entries(options)) {
    const select = document.querySelector(`[data-filter="${key}"]`);
    const priorValue = select.value;
    select.innerHTML = `<option value="">${placeholders[key]}</option>${values.map((value) => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join("")}`;
    if (values.includes(priorValue)) select.value = priorValue;
  }
}

async function refreshDashboard() {
  const requestId = ++pendingRequest;
  const params = new URLSearchParams();
  document.querySelectorAll("[data-filter]").forEach((select) => {
    if (select.value) params.set(select.dataset.filter, select.value);
  });
  document.querySelector("#dashboard-content").innerHTML = `<div class="empty">Querying the local warehouse…</div>`;
  try {
    const response = await fetch(`/api/dashboard?${params.toString()}`, { cache: "no-store" });
    const data = await response.json();
    if (requestId !== pendingRequest) return;
    if (!response.ok) throw new Error(data.error || `Dashboard API returned ${response.status}`);
    latestData = data;
    populateOptions(data.options);
    document.querySelector("#date-range").textContent = `${data.metadata.order_date_start} — ${data.metadata.order_date_end}`;
    document.querySelector("#page-title").textContent = pageTitles[currentPage];
    renderKpis(data);
    renderPage(data);
    const selected = Object.keys(data.filters);
    document.querySelector("#filter-note").textContent = selected.length ? `Filters: ${selected.join(", ")}` : "All data";
  } catch (error) {
    document.querySelector("#dashboard-content").innerHTML = `<div class="error">Dashboard data could not be loaded: ${escapeHtml(error.message)}</div>`;
  }
}

document.querySelector("#page-nav").addEventListener("click", (event) => {
  const button = event.target.closest("[data-page]");
  if (!button) return;
  currentPage = button.dataset.page;
  document.querySelectorAll(".nav-item").forEach((item) =>
    item.classList.toggle("active", item === button)
  );
  if (latestData) {
    document.querySelector("#page-title").textContent = pageTitles[currentPage];
    renderKpis(latestData);
    renderPage(latestData);
  } else {
    refreshDashboard();
  }
});
document.querySelectorAll("[data-filter]").forEach((select) =>
  select.addEventListener("change", refreshDashboard)
);
document.querySelector("#reset-filters").addEventListener("click", () => {
  document.querySelectorAll("[data-filter]").forEach((select) => { select.value = ""; });
  refreshDashboard();
});
refreshDashboard();
