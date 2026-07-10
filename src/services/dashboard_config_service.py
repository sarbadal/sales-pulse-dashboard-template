from __future__ import annotations

from pathlib import Path

import yaml

from src.constants import (
    ACTIVE_CONFIG_OPTIONS_YAML,
    ACTIVE_CONFIG_SELECTOR_YAML,
    CONFIG_DIR,
    DEFAULT_CONFIG_FILENAME,
    DEFAULT_CONFIG_YAML,
    VALID_CAMPAIGN_CHANNEL_CHART_TYPES,
    VALID_CAMPAIGN_CHANNEL_PERFORMANCE_MODES,
    VALID_ORDER_STATUS_CHART_TYPES,
    VALID_REGION_CHART_TYPES,
    VALID_REVENUE_TREND_STYLES,
    VALID_SEGMENT_CHART_TYPES,
)
from src.utils.config_helpers import merge_dict, read_yaml_dict
from src.utils.dashboard_config_builders import (
    default_dashboard_config,
    extract_branding_config,
    extract_campaign_channel_performance_config,
    extract_latest_table_config,
    extract_revenue_trend_config,
    extract_top_products_config,
    extract_typed_color_chart_config,
)


def list_available_dashboard_configs() -> list[str]:
    if not CONFIG_DIR.exists():
        return [DEFAULT_CONFIG_FILENAME]

    config_files = sorted(
        path.name
        for path in CONFIG_DIR.glob("*.yaml")
        if path.name != ACTIVE_CONFIG_SELECTOR_YAML.name
    )
    return config_files or [DEFAULT_CONFIG_FILENAME]


def get_selected_dashboard_config_filename() -> str:
    if not ACTIVE_CONFIG_SELECTOR_YAML.exists():
        return DEFAULT_CONFIG_FILENAME

    try:
        with ACTIVE_CONFIG_SELECTOR_YAML.open("r", encoding="utf-8") as selector_file:
            raw_selector = yaml.safe_load(selector_file) or {}
    except (OSError, yaml.YAMLError):
        return DEFAULT_CONFIG_FILENAME

    selected_filename = str(raw_selector.get("selected_config", "")).strip()
    available = set(list_available_dashboard_configs())
    if selected_filename in available:
        return selected_filename

    return DEFAULT_CONFIG_FILENAME


def set_selected_dashboard_config_filename(config_filename: str) -> bool:
    normalized = str(config_filename).strip()
    if normalized not in set(list_available_dashboard_configs()):
        return False

    selector_payload = {"selected_config": normalized}
    try:
        with ACTIVE_CONFIG_SELECTOR_YAML.open("w", encoding="utf-8") as selector_file:
            yaml.safe_dump(selector_payload, selector_file, sort_keys=False)
    except OSError:
        return False

    return True


def get_active_dashboard_option_overrides() -> dict:
    return read_yaml_dict(ACTIVE_CONFIG_OPTIONS_YAML)


def set_active_dashboard_option_overrides(option_overrides: dict) -> bool:
    if not isinstance(option_overrides, dict):
        return False

    try:
        with ACTIVE_CONFIG_OPTIONS_YAML.open("w", encoding="utf-8") as options_file:
            yaml.safe_dump(option_overrides, options_file, sort_keys=False)
    except OSError:
        return False

    return True


def resolve_dashboard_config_path() -> Path:
    selected_filename = get_selected_dashboard_config_filename()
    selected_path = CONFIG_DIR / selected_filename
    if selected_path.exists():
        return selected_path

    return DEFAULT_CONFIG_YAML


def load_dashboard_config() -> dict:
    default_config = default_dashboard_config()

    config_yaml = resolve_dashboard_config_path()

    if not config_yaml.exists():
        return default_config

    try:
        with config_yaml.open("r", encoding="utf-8") as config_file:
            raw_config = yaml.safe_load(config_file) or {}
    except (OSError, yaml.YAMLError):
        return default_config

    if not isinstance(raw_config, dict):
        return default_config

    active_option_overrides = get_active_dashboard_option_overrides()
    if active_option_overrides:
        raw_config = merge_dict(raw_config, active_option_overrides)

    revenue_trend_config = extract_revenue_trend_config(
        raw_config,
        default_config,
        VALID_REVENUE_TREND_STYLES,
    )
    region_config = extract_typed_color_chart_config(
        raw_config,
        default_config,
        "revenue_by_region",
        VALID_REGION_CHART_TYPES,
    )
    order_status_config = extract_typed_color_chart_config(
        raw_config,
        default_config,
        "order_status",
        VALID_ORDER_STATUS_CHART_TYPES,
    )
    segment_config = extract_typed_color_chart_config(
        raw_config,
        default_config,
        "revenue_by_segment",
        VALID_SEGMENT_CHART_TYPES,
    )
    campaign_channel_config = extract_campaign_channel_performance_config(
        raw_config,
        default_config,
        VALID_CAMPAIGN_CHANNEL_PERFORMANCE_MODES,
        VALID_CAMPAIGN_CHANNEL_CHART_TYPES,
    )
    top_products_config = extract_top_products_config(raw_config, default_config)
    latest_sales_config = extract_latest_table_config(raw_config, default_config, "latest_sales_orders")
    latest_campaigns_config = extract_latest_table_config(raw_config, default_config, "latest_campaigns")
    branding_config = extract_branding_config(raw_config, default_config)

    return {
        "branding": branding_config,
        "charts": {
            "revenue_trend": revenue_trend_config,
            "revenue_by_region": region_config,
            "order_status": order_status_config,
            "revenue_by_segment": segment_config,
            "campaign_channel_performance": campaign_channel_config,
            "top_products_by_units": top_products_config,
            "latest_sales_orders": latest_sales_config,
            "latest_campaigns": latest_campaigns_config,
        },
    }
