from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SALES_CSV = BASE_DIR / "data" / "sample_sales.csv"
ORDERS_CSV = BASE_DIR / "data" / "sample_orders.csv"
CONFIG_YAML = BASE_DIR / "config" / "dashboard_config.yaml"
VALID_TREND_GRAIN = {"daily", "weekly", "monthly"}
VALID_REVENUE_TREND_STYLES = {"line", "area"}
VALID_REGION_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}


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


def build_dashboard_data(trend_granularity: str = "daily") -> dict:
    selected_trend = trend_granularity if trend_granularity in VALID_TREND_GRAIN else "daily"
    dashboard_config = load_dashboard_config()
    sales_rows = read_csv_rows(SALES_CSV)
    orders_rows = read_csv_rows(ORDERS_CSV)

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

    top_products = sorted(units_by_product.items(), key=lambda x: x[1], reverse=True)[:5]

    return {
        "kpis": {
            "total_revenue": round(total_revenue, 2),
            "total_profit": round(total_profit, 2),
            "total_orders": total_orders,
            "avg_order_value": round(avg_order_value, 2),
        },
        "revenue_trend": aggregate_revenue_trend(sales_rows, selected_trend),
        "chart_config": {
            "revenue_trend_style": dashboard_config["charts"]["revenue_trend"]["style"],
            "revenue_trend_line_color": dashboard_config["charts"]["revenue_trend"]["line_color"],
            "revenue_trend_area_color": dashboard_config["charts"]["revenue_trend"]["area_color"],
            "revenue_by_region_type": dashboard_config["charts"]["revenue_by_region"]["type"],
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
        "latest_sales": sales_rows[-8:],
    }
