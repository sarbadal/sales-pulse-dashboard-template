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
- `charts.campaign_channel_performance.mode`: `combined` or `split`.
- `charts.campaign_channel_performance.split_spend_type`: `donut`, `pie`, `vertical_bar`, or `horizontal_bar` (used when mode is `split`).
- `charts.campaign_channel_performance.split_revenue_type`: `donut`, `pie`, `vertical_bar`, or `horizontal_bar` (used when mode is `split`).
- `charts.*.colors`: Color list used in region/segment/status charts.
- `charts.top_products_by_units.top_n`: Positive integer for number of products.
- `charts.top_products_by_units.color`: Single bar color for top products chart.
- `charts.top_products_by_units.include_others`: `true` or `false` to show/hide Others bar.
- `charts.latest_sales_orders.last_n_rows`: Positive integer for rows in latest orders table.
- `charts.latest_sales_orders.show_table`: `true` or `false` to show/hide Latest Sales Orders table.
- `charts.latest_campaigns.last_n_rows`: Positive integer for rows in latest campaigns table.
- `charts.latest_campaigns.show_table`: `true` or `false` to show/hide Latest Campaigns table.

### Notes

- Keep YAML indentation with spaces.
- Use valid YAML values (`true`/`false`, numbers without quotes when possible).
- Restart the app after config changes.

## Revenue + Campaign ROAS Trend Logic

The combined trend chart plots:

- Revenue (from sales CSV)
- Campaign ROAS (recomputed from campaign spend/revenue)

Campaign ROAS continuity is calculated from active campaign date ranges (`start_date` to `end_date`) instead of only campaign start dates.

### How Campaign ROAS Is Computed

1. For each campaign row:
	- Parse `start_date` and `end_date`.
	- Compute campaign duration in days:
	  - `campaign_days = (end_date - start_date) + 1`
	- Distribute totals uniformly across campaign days:
	  - `daily_spend = spend / campaign_days`
	  - `daily_revenue = revenue / campaign_days`

2. For each day in the campaign range:
	- Map the day into the selected bucket (`daily`, `weekly`, `monthly`).
	- Add `daily_spend` and `daily_revenue` to that bucket totals.

3. After all campaigns are processed, compute bucket ROAS:
	- `roas_bucket = total_revenue_bucket / total_spend_bucket`
	- Rounded to 2 decimals.

### Granularity Bucketing Rules

- `daily`: exact date bucket
- `weekly`: Monday-start week bucket
- `monthly`: first day of month bucket

### Important Note

The trend chart uses recomputed ROAS from aggregated spend/revenue per bucket. It does not directly plot the row-level `roas` column from the campaign CSV.

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
