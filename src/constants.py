from __future__ import annotations

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"
SALES_CSV = BASE_DIR / "data" / "sample_sales.csv"
ORDERS_CSV = BASE_DIR / "data" / "sample_orders.csv"
CAMPAIGNS_CSV = BASE_DIR / "data" / "sample_campaign_performance.csv"
DEFAULT_CONFIG_FILENAME = "dashboard_config.yaml"
DEFAULT_CONFIG_YAML = CONFIG_DIR / DEFAULT_CONFIG_FILENAME
ACTIVE_CONFIG_SELECTOR_YAML = CONFIG_DIR / "active_dashboard_config.yaml"
ACTIVE_CONFIG_OPTIONS_YAML = CONFIG_DIR / "active_dashboard_options.yaml"
VALID_TREND_GRAIN = {"daily", "weekly", "monthly"}
VALID_REVENUE_TREND_STYLES = {"line", "area"}
VALID_REGION_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}
VALID_ORDER_STATUS_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}
VALID_SEGMENT_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}
VALID_CAMPAIGN_CHANNEL_PERFORMANCE_MODES = {"combined", "split"}
VALID_CAMPAIGN_CHANNEL_CHART_TYPES = {"donut", "vertical_bar", "horizontal_bar", "pie"}
