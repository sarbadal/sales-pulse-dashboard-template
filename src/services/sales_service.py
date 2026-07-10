from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALES_CSV = BASE_DIR / "data" / "sample_sales.csv"
ORDERS_CSV = BASE_DIR / "data" / "sample_orders.csv"
CAMPAIGNS_CSV = BASE_DIR / "data" / "sample_campaign_performance.csv"
CONFIG_YAML = BASE_DIR / "config" / "dashboard_config.yaml"
VALID_TREND_GRAIN = {"daily", "weekly", "monthly"}
VALID_REVENUE_TREND_STYLES = {"line", "area"}
VALID_REGION_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}
VALID_ORDER_STATUS_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}
VALID_SEGMENT_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}


def _normalize_color(value: object, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback

    normalized = value.strip()
    if not normalized:
        return fallback

    return normalized


def _normalize_text(value: object, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback

    normalized = value.strip()
    if not normalized:
        return fallback

    return normalized


def _normalize_color_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback

    normalized_colors = [
        item.strip() for item in value if isinstance(item, str) and item.strip()
    ]
    return normalized_colors or fallback


def _normalize_bool(value: object, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False

    return fallback


def _normalize_positive_int(value: object, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return parsed if parsed > 0 else fallback


def _to_float(value: str) -> float:
    return float(value.strip() or 0)


def _to_int(value: str) -> int:
    return int(float(value.strip() or 0))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []

    with path.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)


def load_dashboard_config() -> dict:
    default_config = {
        "branding": {
            "dashboard_title": "Sales Pulse Dashboard",
            "dashboard_title_color": "#1f2435",
        },
        "charts": {
            "revenue_trend": {
                "style": "area",
                "line_color": "#1a7f5a",
                "area_color": "rgba(26, 127, 90, 0.15)",
            },
            "revenue_by_region": {
                "type": "donut",
                "colors": ["#1a7f5a", "#2f6f91", "#ed8d21", "#b93c5d"],
            },
            "order_status": {
                "type": "vertical_bar",
                "colors": ["#2f6f91", "#ed8d21", "#1a7f5a", "#b93c5d"],
            },
            "revenue_by_segment": {
                "type": "pie",
                "colors": ["#b93c5d", "#ed8d21", "#1a7f5a", "#2f6f91"],
            },
            "top_products_by_units": {
                "top_n": 5,
                "color": "#2f6f91",
                "include_others": False,
            },
            "latest_sales_orders": {
                "last_n_rows": 8,
            },
        }
    }

    if not CONFIG_YAML.exists():
        return default_config

    try:
        with CONFIG_YAML.open("r", encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file) or {}
    except (OSError, yaml.YAMLError):
        return default_config

    if not isinstance(raw_config, dict):
        return default_config

    style = (
        raw_config.get("charts", {})
        .get("revenue_trend", {})
        .get("style", default_config["charts"]["revenue_trend"]["style"])
    )
    style = str(style).strip().lower()

    if style not in VALID_REVENUE_TREND_STYLES:
        style = default_config["charts"]["revenue_trend"]["style"]

    region_chart_type = (
        raw_config.get("charts", {})
        .get("revenue_by_region", {})
        .get("type", default_config["charts"]["revenue_by_region"]["type"])
    )
    region_chart_type = str(region_chart_type).strip().lower()
    if region_chart_type not in VALID_REGION_CHART_TYPES:
        region_chart_type = default_config["charts"]["revenue_by_region"]["type"]

    region_colors = _normalize_color_list(
        raw_config.get("charts", {}).get("revenue_by_region", {}).get("colors"),
        default_config["charts"]["revenue_by_region"]["colors"],
    )

    order_status_chart_type = (
        raw_config.get("charts", {})
        .get("order_status", {})
        .get("type", default_config["charts"]["order_status"]["type"])
    )
    order_status_chart_type = str(order_status_chart_type).strip().lower()
    if order_status_chart_type not in VALID_ORDER_STATUS_CHART_TYPES:
        order_status_chart_type = default_config["charts"]["order_status"]["type"]

    order_status_colors = _normalize_color_list(
        raw_config.get("charts", {}).get("order_status", {}).get("colors"),
        default_config["charts"]["order_status"]["colors"],
    )

    segment_chart_type = (
        raw_config.get("charts", {})
        .get("revenue_by_segment", {})
        .get("type", default_config["charts"]["revenue_by_segment"]["type"])
    )
    segment_chart_type = str(segment_chart_type).strip().lower()
    if segment_chart_type not in VALID_SEGMENT_CHART_TYPES:
        segment_chart_type = default_config["charts"]["revenue_by_segment"]["type"]

    segment_colors = _normalize_color_list(
        raw_config.get("charts", {}).get("revenue_by_segment", {}).get("colors"),
        default_config["charts"]["revenue_by_segment"]["colors"],
    )

    top_products_top_n = _normalize_positive_int(
        raw_config.get("charts", {}).get("top_products_by_units", {}).get("top_n"),
        default_config["charts"]["top_products_by_units"]["top_n"],
    )
    top_products_color = _normalize_color(
        raw_config.get("charts", {}).get("top_products_by_units", {}).get("color"),
        default_config["charts"]["top_products_by_units"]["color"],
    )
    top_products_include_others = _normalize_bool(
        raw_config.get("charts", {}).get("top_products_by_units", {}).get("include_others"),
        default_config["charts"]["top_products_by_units"]["include_others"],
    )

    latest_sales_last_n_rows = _normalize_positive_int(
        raw_config.get("charts", {}).get("latest_sales_orders", {}).get("last_n_rows"),
        default_config["charts"]["latest_sales_orders"]["last_n_rows"],
    )

    dashboard_title = _normalize_text(
        raw_config.get("branding", {}).get("dashboard_title"),
        default_config["branding"]["dashboard_title"],
    )
    dashboard_title_color = _normalize_color(
        raw_config.get("branding", {}).get("dashboard_title_color"),
        default_config["branding"]["dashboard_title_color"],
    )

    line_color = _normalize_color(
        raw_config.get("charts", {}).get("revenue_trend", {}).get("line_color"),
        default_config["charts"]["revenue_trend"]["line_color"],
    )
    area_color = _normalize_color(
        raw_config.get("charts", {}).get("revenue_trend", {}).get("area_color"),
        default_config["charts"]["revenue_trend"]["area_color"],
    )

    return {
        "branding": {
            "dashboard_title": dashboard_title,
            "dashboard_title_color": dashboard_title_color,
        },
        "charts": {
            "revenue_trend": {
                "style": style,
                "line_color": line_color,
                "area_color": area_color,
            },
            "revenue_by_region": {
                "type": region_chart_type,
                "colors": region_colors,
            },
            "order_status": {
                "type": order_status_chart_type,
                "colors": order_status_colors,
            },
            "revenue_by_segment": {
                "type": segment_chart_type,
                "colors": segment_colors,
            },
            "top_products_by_units": {
                "top_n": top_products_top_n,
                "color": top_products_color,
                "include_others": top_products_include_others,
            },
            "latest_sales_orders": {
                "last_n_rows": latest_sales_last_n_rows,
            },
        }
    }


def _parse_iso_date(value: str) -> date | None:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def aggregate_revenue_trend(sales_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    period = granularity if granularity in VALID_TREND_GRAIN else "daily"
    revenue_by_period: dict[str, float] = defaultdict(float)
    bucket_by_period = {
        "weekly": lambda dt: dt - timedelta(days=dt.weekday()),  # Monday start.
        "monthly": lambda dt: dt.replace(day=1),
    }
    resolve_bucket = bucket_by_period.get(period, lambda dt: dt)

    for row in sales_rows:
        current_date = _parse_iso_date(row.get("date", ""))
        if not current_date:
            continue

        bucket_date = resolve_bucket(current_date)

        revenue_by_period[bucket_date.isoformat()] += _to_float(row.get("revenue", "0"))

    sorted_points = sorted(revenue_by_period.items(), key=lambda point: point[0])

    return {
        "labels": [label for label, _ in sorted_points],
        "values": [round(value, 2) for _, value in sorted_points],
    }


def aggregate_campaign_roas_trend(campaign_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    period = granularity if granularity in VALID_TREND_GRAIN else "daily"
    spend_by_period: dict[str, float] = defaultdict(float)
    revenue_by_period: dict[str, float] = defaultdict(float)
    bucket_by_period = {
        "weekly": lambda dt: dt - timedelta(days=dt.weekday()),  # Monday start.
        "monthly": lambda dt: dt.replace(day=1),
    }
    resolve_bucket = bucket_by_period.get(period, lambda dt: dt)

    for row in campaign_rows:
        start_date = _parse_iso_date(row.get("start_date", ""))
        end_date = _parse_iso_date(row.get("end_date", ""))
        if not start_date or not end_date or end_date < start_date:
            continue

        total_spend = _to_float(row.get("spend", "0"))
        total_revenue = _to_float(row.get("revenue", "0"))
        campaign_days = (end_date - start_date).days + 1
        if campaign_days <= 0:
            continue

        daily_spend = total_spend / campaign_days
        daily_revenue = total_revenue / campaign_days

        current_day = start_date
        while current_day <= end_date:
            bucket_date = resolve_bucket(current_day)
            bucket_label = bucket_date.isoformat()
            spend_by_period[bucket_label] += daily_spend
            revenue_by_period[bucket_label] += daily_revenue
            current_day += timedelta(days=1)

    sorted_labels = sorted(revenue_by_period.keys())
    roas_values = [
        round(revenue_by_period[label] / spend_by_period[label], 2)
        if spend_by_period[label]
        else 0
        for label in sorted_labels
    ]

    return {
        "labels": sorted_labels,
        "values": roas_values,
    }


def aggregate_campaign_spend_trend(campaign_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    period = granularity if granularity in VALID_TREND_GRAIN else "daily"
    spend_by_period: dict[str, float] = defaultdict(float)
    bucket_by_period = {
        "weekly": lambda dt: dt - timedelta(days=dt.weekday()),  # Monday start.
        "monthly": lambda dt: dt.replace(day=1),
    }
    resolve_bucket = bucket_by_period.get(period, lambda dt: dt)

    for row in campaign_rows:
        start_date = _parse_iso_date(row.get("start_date", ""))
        end_date = _parse_iso_date(row.get("end_date", ""))
        if not start_date or not end_date or end_date < start_date:
            continue

        total_spend = _to_float(row.get("spend", "0"))
        campaign_days = (end_date - start_date).days + 1
        if campaign_days <= 0:
            continue

        daily_spend = total_spend / campaign_days

        current_day = start_date
        while current_day <= end_date:
            bucket_date = resolve_bucket(current_day)
            bucket_label = bucket_date.isoformat()
            spend_by_period[bucket_label] += daily_spend
            current_day += timedelta(days=1)

    sorted_labels = sorted(spend_by_period.keys())

    return {
        "labels": sorted_labels,
        "values": [round(spend_by_period[label], 2) for label in sorted_labels],
    }


def build_dashboard_data(trend_granularity: str = "daily") -> dict:
    selected_trend = trend_granularity if trend_granularity in VALID_TREND_GRAIN else "daily"
    dashboard_config = load_dashboard_config()
    sales_rows = read_csv_rows(SALES_CSV)
    orders_rows = read_csv_rows(ORDERS_CSV)
    campaign_rows = read_csv_rows(CAMPAIGNS_CSV)

    total_revenue = sum(_to_float(row.get("revenue", "0")) for row in sales_rows)
    total_profit = sum(_to_float(row.get("profit", "0")) for row in sales_rows)
    total_orders = len(sales_rows)
    avg_order_value = total_revenue / total_orders if total_orders else 0

    revenue_by_region: dict[str, float] = defaultdict(float)
    units_by_product: dict[str, int] = defaultdict(int)
    revenue_by_segment: dict[str, float] = defaultdict(float)

    for row in sales_rows:
        region = row.get("region", "Unknown")
        product = row.get("product", "Unknown")
        segment = row.get("customer_segment", "Unknown")
        revenue = _to_float(row.get("revenue", "0"))
        units = _to_int(row.get("units_sold", "0"))

        revenue_by_region[region] += revenue
        units_by_product[product] += units
        revenue_by_segment[segment] += revenue

    status_counts: dict[str, int] = defaultdict(int)
    for row in orders_rows:
        status = row.get("order_status", "Unknown")
        status_counts[status] += 1

    campaign_spend = sum(_to_float(row.get("spend", "0")) for row in campaign_rows)
    campaign_revenue = sum(_to_float(row.get("revenue", "0")) for row in campaign_rows)
    campaign_conversions = sum(_to_int(row.get("conversions", "0")) for row in campaign_rows)
    campaign_clicks = sum(_to_int(row.get("clicks", "0")) for row in campaign_rows)
    avg_campaign_roas = campaign_revenue / campaign_spend if campaign_spend else 0

    spend_by_channel: dict[str, float] = defaultdict(float)
    revenue_by_channel: dict[str, float] = defaultdict(float)

    for row in campaign_rows:
        channel = row.get("channel", "Unknown")
        spend_by_channel[channel] += _to_float(row.get("spend", "0"))
        revenue_by_channel[channel] += _to_float(row.get("revenue", "0"))

    top_products_top_n = dashboard_config["charts"]["top_products_by_units"]["top_n"]
    include_others = dashboard_config["charts"]["top_products_by_units"]["include_others"]
    latest_sales_last_n_rows = dashboard_config["charts"]["latest_sales_orders"]["last_n_rows"]
    sorted_channels = sorted(
        spend_by_channel.keys(),
        key=lambda channel_name: revenue_by_channel[channel_name],
        reverse=True,
    )
    latest_campaigns = sorted(
        campaign_rows,
        key=lambda row: row.get("start_date", ""),
        reverse=True,
    )[:latest_sales_last_n_rows]
    ranked_products = sorted(units_by_product.items(), key=lambda x: x[1], reverse=True)
    top_products = ranked_products[:top_products_top_n]
    if include_others and len(ranked_products) > top_products_top_n:
        others_units = sum(value for _, value in ranked_products[top_products_top_n:])
        if others_units > 0:
            top_products.append(("Others", others_units))

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
            "top_products_by_units_top_n": top_products_top_n,
            "top_products_by_units_color": dashboard_config["charts"]["top_products_by_units"]["color"],
            "top_products_by_units_include_others": include_others,
            "latest_sales_orders_last_n_rows": latest_sales_last_n_rows,
        },
        "branding": {
            "dashboard_title": dashboard_config["branding"]["dashboard_title"],
            "dashboard_title_color": dashboard_config["branding"]["dashboard_title_color"],
        },
        "selected_trend": selected_trend,
        "region_breakdown": {
            "labels": list(revenue_by_region.keys()),
            "values": [round(value, 2) for value in revenue_by_region.values()],
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
