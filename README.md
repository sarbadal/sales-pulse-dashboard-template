# Sales Dashboard (Flask)

Simple Flask dashboard that reads sales data from CSV files.

## Configuration (YAML)

The dashboard behavior is controlled by:

- `config/dashboard_config.yaml`

Edit this file to change title text, chart styles, colors, and table size.

### What you are expected to change

- `branding.dashboard_title`: Dashboard heading and browser tab title.
- `branding.dashboard_title_color`: Title color (hex, rgb/rgba, or color name).
- `charts.revenue_trend.style`: `line` or `area`.
- `charts.revenue_trend.line_color`, `charts.revenue_trend.area_color`: Trend chart colors.
- `charts.revenue_by_region.type`: `donut`, `pie`, `vertical_bar`, or `horizontal_bar`.
- `charts.revenue_by_segment.type`: `donut`, `pie`, `vertical_bar`, or `horizontal_bar`.
- `charts.order_status.type`: `donut`, `pie`, `vertical_bar`, or `horizontal_bar`.
- `charts.*.colors`: Color list used in region/segment/status charts.
- `charts.top_products_by_units.top_n`: Positive integer for number of products.
- `charts.top_products_by_units.color`: Single bar color for top products chart.
- `charts.top_products_by_units.include_others`: `true` or `false` to show/hide Others bar.
- `charts.latest_sales_orders.last_n_rows`: Positive integer for rows in latest orders table.

### Notes

- Keep YAML indentation with spaces.
- Use valid YAML values (`true`/`false`, numbers without quotes when possible).
- Restart the app after config changes.

## Run locally

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
python main.py
```

4. Open in browser:

http://127.0.0.1:5000
