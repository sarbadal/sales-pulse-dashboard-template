from __future__ import annotations

from collections import defaultdict

from src.constants import CAMPAIGNS_CSV, ORDERS_CSV, SALES_CSV, VALID_TREND_GRAIN
from src.services.csv_data_service import read_csv_rows
from src.services.dashboard_aggregation_service import (
    aggregate_campaign_roas_trend,
    aggregate_campaign_spend_trend,
    aggregate_revenue_trend,
)
from src.services.dashboard_config_service import load_dashboard_config
from src.utils.number_helpers import to_float, to_int


def build_dashboard_data(trend_granularity: str = "daily") -> dict:
    selected_trend = trend_granularity if trend_granularity in VALID_TREND_GRAIN else "daily"
    dashboard_config = load_dashboard_config()
    sales_rows = read_csv_rows(SALES_CSV)
    orders_rows = read_csv_rows(ORDERS_CSV)
    campaign_rows = read_csv_rows(CAMPAIGNS_CSV)

    total_revenue = sum(to_float(row.get("revenue", "0")) for row in sales_rows)
    total_profit = sum(to_float(row.get("profit", "0")) for row in sales_rows)
    total_orders = len(sales_rows)
    avg_order_value = total_revenue / total_orders if total_orders else 0

    revenue_by_region: dict[str, float] = defaultdict(float)
    units_by_product: dict[str, int] = defaultdict(int)
    revenue_by_segment: dict[str, float] = defaultdict(float)

    for row in sales_rows:
        region = row.get("region", "Unknown")
        product = row.get("product", "Unknown")
        segment = row.get("customer_segment", "Unknown")
        revenue = to_float(row.get("revenue", "0"))
        units = to_int(row.get("units_sold", "0"))

        revenue_by_region[region] += revenue
        units_by_product[product] += units
        revenue_by_segment[segment] += revenue

    status_counts: dict[str, int] = defaultdict(int)
    for row in orders_rows:
        status = row.get("order_status", "Unknown")
        status_counts[status] += 1

    campaign_spend = sum(to_float(row.get("spend", "0")) for row in campaign_rows)
    campaign_revenue = sum(to_float(row.get("revenue", "0")) for row in campaign_rows)
    campaign_conversions = sum(to_int(row.get("conversions", "0")) for row in campaign_rows)
    campaign_clicks = sum(to_int(row.get("clicks", "0")) for row in campaign_rows)
    avg_campaign_roas = campaign_revenue / campaign_spend if campaign_spend else 0

    spend_by_channel: dict[str, float] = defaultdict(float)
    revenue_by_channel: dict[str, float] = defaultdict(float)
    spend_by_region: dict[str, float] = defaultdict(float)

    for row in campaign_rows:
        channel = row.get("channel", "Unknown")
        region = row.get("region", "Unknown")
        spend_by_channel[channel] += to_float(row.get("spend", "0"))
        revenue_by_channel[channel] += to_float(row.get("revenue", "0"))
        spend_by_region[region] += to_float(row.get("spend", "0"))

    top_products_top_n = dashboard_config["charts"]["top_products_by_units"]["top_n"]
    include_others = dashboard_config["charts"]["top_products_by_units"]["include_others"]
    latest_sales_last_n_rows = dashboard_config["charts"]["latest_sales_orders"]["last_n_rows"]
    latest_campaigns_last_n_rows = dashboard_config["charts"]["latest_campaigns"]["last_n_rows"]
    sorted_channels = sorted(
        spend_by_channel.keys(),
        key=lambda channel_name: revenue_by_channel[channel_name],
        reverse=True,
    )
    latest_campaigns = sorted(
        campaign_rows,
        key=lambda row: row.get("start_date", ""),
        reverse=True,
    )[:latest_campaigns_last_n_rows]
    ranked_products = sorted(units_by_product.items(), key=lambda x: x[1], reverse=True)
    top_products = ranked_products[:top_products_top_n]
    if include_others and len(ranked_products) > top_products_top_n:
        others_units = sum(value for _, value in ranked_products[top_products_top_n:])
        if others_units > 0:
            top_products.append(("Others", others_units))

    region_labels = list(revenue_by_region.keys())
    for region in spend_by_region:
        if region not in revenue_by_region:
            region_labels.append(region)

    return {
        "kpis": {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "total_orders": total_orders,
            "avg_order_value": round(avg_order_value, 2),
        },
        "revenue_trend": aggregate_revenue_trend(sales_rows, selected_trend),
        "campaign_kpis": {
            "total_spend": round(campaign_spend, 2),
            "total_campaign_revenue": round(campaign_revenue, 2),
            "total_conversions": campaign_conversions,
            "total_clicks": campaign_clicks,
            "avg_roas": round(avg_campaign_roas, 2),
            "campaign_count": len(campaign_rows),
        },
        "campaign_channel_performance": {
            "labels": sorted_channels,
            "spend_values": [round(spend_by_channel[channel], 2) for channel in sorted_channels],
            "revenue_values": [round(revenue_by_channel[channel], 2) for channel in sorted_channels],
        },
        "campaign_roas_trend": aggregate_campaign_roas_trend(campaign_rows, selected_trend),
        "campaign_spend_trend": aggregate_campaign_spend_trend(campaign_rows, selected_trend),
        "chart_config": {
            "revenue_trend_style": dashboard_config["charts"]["revenue_trend"]["style"],
            "revenue_trend_line_color": dashboard_config["charts"]["revenue_trend"]["line_color"],
            "revenue_trend_area_color": dashboard_config["charts"]["revenue_trend"]["area_color"],
            "revenue_by_region_type": dashboard_config["charts"]["revenue_by_region"]["type"],
            "revenue_by_region_colors": dashboard_config["charts"]["revenue_by_region"]["colors"],
            "order_status_type": dashboard_config["charts"]["order_status"]["type"],
            "order_status_colors": dashboard_config["charts"]["order_status"]["colors"],
            "revenue_by_segment_type": dashboard_config["charts"]["revenue_by_segment"]["type"],
            "revenue_by_segment_colors": dashboard_config["charts"]["revenue_by_segment"]["colors"],
            "campaign_channel_performance_mode": dashboard_config["charts"]["campaign_channel_performance"]["mode"],
            "campaign_channel_performance_split_spend_type": dashboard_config["charts"][
                "campaign_channel_performance"
            ]["split_spend_type"],
            "campaign_channel_performance_split_revenue_type": dashboard_config["charts"][
                "campaign_channel_performance"
            ]["split_revenue_type"],
            "top_products_by_units_top_n": top_products_top_n,
            "top_products_by_units_color": dashboard_config["charts"]["top_products_by_units"]["color"],
            "top_products_by_units_include_others": include_others,
            "latest_sales_orders_last_n_rows": latest_sales_last_n_rows,
            "latest_sales_orders_show_table": dashboard_config["charts"]["latest_sales_orders"][
                "show_table"
            ],
            "latest_campaigns_last_n_rows": latest_campaigns_last_n_rows,
            "latest_campaigns_show_table": dashboard_config["charts"]["latest_campaigns"][
                "show_table"
            ],
        },
        "branding": {
            "dashboard_title": dashboard_config["branding"]["dashboard_title"],
            "dashboard_title_color": dashboard_config["branding"]["dashboard_title_color"],
        },
        "selected_trend": selected_trend,
        "region_breakdown": {
            "labels": region_labels,
            "values": [round(revenue_by_region.get(region, 0), 2) for region in region_labels],
            "campaign_spend_values": [
                round(spend_by_region.get(region, 0), 2) for region in region_labels
            ],
        },
        "segment_breakdown": {
            "labels": list(revenue_by_segment.keys()),
            "values": [round(value, 2) for value in revenue_by_segment.values()],
        },
        "top_products": {
            "labels": [name for name, _ in top_products],
            "values": [value for _, value in top_products],
        },
        "order_status": {
            "labels": list(status_counts.keys()),
            "values": list(status_counts.values()),
        },
        "latest_sales": sales_rows[-latest_sales_last_n_rows:],
        "latest_campaigns": latest_campaigns,
    }
