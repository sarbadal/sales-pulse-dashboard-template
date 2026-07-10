from __future__ import annotations

from src.utils.config_helpers import (
    normalize_bool,
    normalize_choice,
    normalize_color,
    normalize_color_list,
    normalize_positive_int,
    normalize_text,
)


def default_dashboard_config() -> dict:
    return {
        "branding": {
            "dashboard_title": "Sales and Campaign Performance Dashboard",
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
            "campaign_channel_performance": {
                "mode": "combined",
                "split_spend_type": "vertical_bar",
                "split_revenue_type": "vertical_bar",
            },
            "top_products_by_units": {
                "top_n": 5,
                "color": "#2f6f91",
                "include_others": False,
            },
            "latest_sales_orders": {
                "last_n_rows": 8,
                "show_table": True,
            },
            "latest_campaigns": {
                "last_n_rows": 8,
                "show_table": True,
            },
        },
    }


def extract_revenue_trend_config(
    raw_config: dict,
    default_config: dict,
    valid_revenue_trend_styles: set[str],
) -> dict:
    fallback = default_config["charts"]["revenue_trend"]
    style = normalize_choice(
        raw_config.get("charts", {}).get("revenue_trend", {}).get("style", fallback["style"]),
        valid_revenue_trend_styles,
        fallback["style"],
    )
    line_color = normalize_color(
        raw_config.get("charts", {}).get("revenue_trend", {}).get("line_color"),
        fallback["line_color"],
    )
    area_color = normalize_color(
        raw_config.get("charts", {}).get("revenue_trend", {}).get("area_color"),
        fallback["area_color"],
    )
    return {
        "style": style,
        "line_color": line_color,
        "area_color": area_color,
    }


def extract_typed_color_chart_config(
    raw_config: dict,
    default_config: dict,
    chart_key: str,
    valid_types: set[str],
) -> dict:
    fallback = default_config["charts"][chart_key]
    chart_type = normalize_choice(
        raw_config.get("charts", {}).get(chart_key, {}).get("type", fallback["type"]),
        valid_types,
        fallback["type"],
    )
    colors = normalize_color_list(
        raw_config.get("charts", {}).get(chart_key, {}).get("colors"),
        fallback["colors"],
    )
    return {
        "type": chart_type,
        "colors": colors,
    }


def extract_campaign_channel_performance_config(
    raw_config: dict,
    default_config: dict,
    valid_modes: set[str],
    valid_chart_types: set[str],
) -> dict:
    fallback = default_config["charts"]["campaign_channel_performance"]
    mode = normalize_choice(
        raw_config.get("charts", {}).get("campaign_channel_performance", {}).get("mode", fallback["mode"]),
        valid_modes,
        fallback["mode"],
    )
    split_spend_type = normalize_choice(
        raw_config.get("charts", {})
        .get("campaign_channel_performance", {})
        .get("split_spend_type", fallback["split_spend_type"]),
        valid_chart_types,
        fallback["split_spend_type"],
    )
    split_revenue_type = normalize_choice(
        raw_config.get("charts", {})
        .get("campaign_channel_performance", {})
        .get("split_revenue_type", fallback["split_revenue_type"]),
        valid_chart_types,
        fallback["split_revenue_type"],
    )
    return {
        "mode": mode,
        "split_spend_type": split_spend_type,
        "split_revenue_type": split_revenue_type,
    }


def extract_top_products_config(raw_config: dict, default_config: dict) -> dict:
    fallback = default_config["charts"]["top_products_by_units"]
    return {
        "top_n": normalize_positive_int(
            raw_config.get("charts", {}).get("top_products_by_units", {}).get("top_n"),
            fallback["top_n"],
        ),
        "color": normalize_color(
            raw_config.get("charts", {}).get("top_products_by_units", {}).get("color"),
            fallback["color"],
        ),
        "include_others": normalize_bool(
            raw_config.get("charts", {}).get("top_products_by_units", {}).get("include_others"),
            fallback["include_others"],
        ),
    }


def extract_latest_table_config(raw_config: dict, default_config: dict, chart_key: str) -> dict:
    fallback = default_config["charts"][chart_key]
    return {
        "last_n_rows": normalize_positive_int(
            raw_config.get("charts", {}).get(chart_key, {}).get("last_n_rows"),
            fallback["last_n_rows"],
        ),
        "show_table": normalize_bool(
            raw_config.get("charts", {}).get(chart_key, {}).get("show_table"),
            fallback["show_table"],
        ),
    }


def extract_branding_config(raw_config: dict, default_config: dict) -> dict:
    fallback = default_config["branding"]
    return {
        "dashboard_title": normalize_text(
            raw_config.get("branding", {}).get("dashboard_title"),
            fallback["dashboard_title"],
        ),
        "dashboard_title_color": normalize_color(
            raw_config.get("branding", {}).get("dashboard_title_color"),
            fallback["dashboard_title_color"],
        ),
    }
