from __future__ import annotations

from datetime import date

import pandas as pd

from src.constants import CAMPAIGNS_CSV, ORDERS_CSV, SALES_CSV, VALID_TREND_GRAIN
from src.services.csv_data_service import read_csv_rows
from src.services.dashboard_aggregation_service import (
    aggregate_campaign_roas_trend,
    aggregate_campaign_spend_trend,
    aggregate_revenue_trend,
)
from src.services.dashboard_config_service import load_dashboard_config
from src.utils.date_helpers import parse_iso_date


def _normalize_label_series(frame: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in frame.columns:
        return pd.Series(["Unknown"] * len(frame), index=frame.index, dtype="object")

    labels = frame[column_name].fillna("Unknown").astype(str).str.strip()
    return labels.where(labels != "", "Unknown")


def _numeric_series(frame: pd.DataFrame, column_name: str) -> pd.Series:
    if column_name not in frame.columns:
        return pd.Series([0] * len(frame), index=frame.index, dtype="float64")

    return pd.to_numeric(frame[column_name], errors="coerce").fillna(0)


def _normalize_date_range(start_date_raw: str | None, end_date_raw: str | None) -> tuple[date | None, date | None]:
    start_date = parse_iso_date((start_date_raw or "").strip())
    end_date = parse_iso_date((end_date_raw or "").strip())

    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date


def _resolve_data_date_bounds(sales_df: pd.DataFrame, orders_df: pd.DataFrame, campaign_df: pd.DataFrame) -> tuple[date | None, date | None]:
    date_candidates: list[pd.Series] = []

    if not sales_df.empty:
        date_candidates.append(pd.to_datetime(sales_df.get("date"), errors="coerce"))

    if not orders_df.empty:
        date_candidates.append(pd.to_datetime(orders_df.get("order_date"), errors="coerce"))

    if not campaign_df.empty:
        date_candidates.append(pd.to_datetime(campaign_df.get("start_date"), errors="coerce"))
        date_candidates.append(pd.to_datetime(campaign_df.get("end_date"), errors="coerce"))

    if not date_candidates:
        return None, None

    all_dates = pd.concat(date_candidates, ignore_index=True).dropna()
    if all_dates.empty:
        return None, None

    return all_dates.min().date(), all_dates.max().date()


def _resolve_region_options(sales_df: pd.DataFrame, campaign_df: pd.DataFrame) -> list[str]:
    regions: set[str] = set()

    if not sales_df.empty:
        regions.update(_normalize_label_series(sales_df, "region").tolist())

    if not campaign_df.empty:
        regions.update(_normalize_label_series(campaign_df, "region").tolist())

    return sorted(region for region in regions if region)


def _normalize_region_filter(region_raw: str | list[str] | tuple[str, ...] | None, available_regions: list[str]) -> list[str]:
    if isinstance(region_raw, str):
        raw_values = [region_raw]
    elif isinstance(region_raw, (list, tuple)):
        raw_values = [str(value) for value in region_raw]
    else:
        raw_values = []

    normalized_candidates = [value.strip() for value in raw_values if value and value.strip()]
    if not normalized_candidates:
        return ["all"]

    if any(value.lower() == "all" for value in normalized_candidates):
        return ["all"]

    selected_regions: list[str] = []
    selected_lookup: set[str] = set()
    for region in available_regions:
        region_lower = region.lower()
        if region_lower in selected_lookup:
            continue
        if any(candidate.lower() == region_lower for candidate in normalized_candidates):
            selected_regions.append(region)
            selected_lookup.add(region_lower)

    return selected_regions or ["all"]


def _apply_region_filter(sales_df: pd.DataFrame, orders_df: pd.DataFrame, campaign_df: pd.DataFrame, selected_regions: list[str]) -> tuple:
    if "all" in selected_regions:
        return sales_df, orders_df, campaign_df

    selected_region_set = set(selected_regions)

    if sales_df.empty:
        filtered_sales_df = sales_df
    else:
        sales_regions = _normalize_label_series(sales_df, "region")
        filtered_sales_df = sales_df[sales_regions.isin(selected_region_set)].copy()

    if campaign_df.empty:
        filtered_campaign_df = campaign_df
    else:
        campaign_regions = _normalize_label_series(campaign_df, "region")
        filtered_campaign_df = campaign_df[campaign_regions.isin(selected_region_set)].copy()

    if orders_df.empty or filtered_sales_df.empty:
        filtered_orders_df = orders_df.iloc[0:0].copy()
    else:
        order_ids = set(filtered_sales_df.get("order_id", pd.Series(dtype="object")).astype(str).tolist())
        filtered_orders_df = orders_df[
            orders_df.get("order_id", pd.Series(dtype="object")).astype(str).isin(order_ids)
        ].copy()

    return filtered_sales_df, filtered_orders_df, filtered_campaign_df


def _filter_dataframes_by_date_range(sales_df: pd.DataFrame, orders_df: pd.DataFrame, campaign_df: pd.DataFrame, start_date: date | None, end_date: date | None) -> tuple:
    if not start_date and not end_date:
        return sales_df, orders_df, campaign_df

    if sales_df.empty:
        filtered_sales_df = sales_df
    else:
        sales_dates = pd.to_datetime(sales_df.get("date"), errors="coerce")
        sales_mask = sales_dates.notna()
        if start_date:
            sales_mask &= sales_dates >= pd.Timestamp(start_date)
        if end_date:
            sales_mask &= sales_dates <= pd.Timestamp(end_date)
        filtered_sales_df = sales_df[sales_mask].copy()

    if orders_df.empty:
        filtered_orders_df = orders_df
    else:
        order_dates = pd.to_datetime(orders_df.get("order_date"), errors="coerce")
        order_mask = order_dates.notna()
        if start_date:
            order_mask &= order_dates >= pd.Timestamp(start_date)
        if end_date:
            order_mask &= order_dates <= pd.Timestamp(end_date)
        filtered_orders_df = orders_df[order_mask].copy()

    if campaign_df.empty:
        filtered_campaign_df = campaign_df
    else:
        campaign_start = pd.to_datetime(campaign_df.get("start_date"), errors="coerce")
        campaign_end = pd.to_datetime(campaign_df.get("end_date"), errors="coerce")
        campaign_mask = campaign_start.notna() & campaign_end.notna()
        if start_date:
            campaign_mask &= campaign_end >= pd.Timestamp(start_date)
        if end_date:
            campaign_mask &= campaign_start <= pd.Timestamp(end_date)
        filtered_campaign_df = campaign_df[campaign_mask].copy()

    return filtered_sales_df, filtered_orders_df, filtered_campaign_df


def build_dashboard_data(
    trend_granularity: str = "daily",
    start_date_raw: str | None = None,
    end_date_raw: str | None = None,
    region_raw: str | list[str] | tuple[str, ...] | None = None,
) -> dict:
    selected_trend = trend_granularity if trend_granularity in VALID_TREND_GRAIN else "daily"
    dashboard_config = load_dashboard_config()
    sales_df = pd.DataFrame(read_csv_rows(SALES_CSV))
    orders_df = pd.DataFrame(read_csv_rows(ORDERS_CSV))
    campaign_df = pd.DataFrame(read_csv_rows(CAMPAIGNS_CSV))
    available_regions = _resolve_region_options(sales_df, campaign_df)
    selected_regions = _normalize_region_filter(region_raw, available_regions)
    data_start_date, data_end_date = _resolve_data_date_bounds(sales_df, orders_df, campaign_df)
    selected_start_date, selected_end_date = _normalize_date_range(start_date_raw, end_date_raw)
    selected_start_date = selected_start_date or data_start_date
    selected_end_date = selected_end_date or data_end_date
    if selected_start_date and selected_end_date and selected_start_date > selected_end_date:
        selected_start_date, selected_end_date = selected_end_date, selected_start_date

    sales_df, orders_df, campaign_df = _filter_dataframes_by_date_range(
        sales_df,
        orders_df,
        campaign_df,
        selected_start_date,
        selected_end_date,
    )
    sales_df, orders_df, campaign_df = _apply_region_filter(
        sales_df,
        orders_df,
        campaign_df,
        selected_regions,
    )
    sales_rows = sales_df.to_dict("records")
    orders_rows = orders_df.to_dict("records")
    campaign_rows = campaign_df.to_dict("records")

    sales_revenue = _numeric_series(sales_df, "revenue")
    sales_profit = _numeric_series(sales_df, "profit")
    sales_units = _numeric_series(sales_df, "units_sold")
    campaign_spend_series = _numeric_series(campaign_df, "spend")
    campaign_revenue_series = _numeric_series(campaign_df, "revenue")
    campaign_conversion_series = _numeric_series(campaign_df, "conversions")
    campaign_click_series = _numeric_series(campaign_df, "clicks")

    total_revenue = float(sales_revenue.sum())
    total_profit = float(sales_profit.sum())
    total_orders = len(sales_rows)
    avg_order_value = total_revenue / total_orders if total_orders else 0

    revenue_by_region = (
        sales_df.assign(
            region=_normalize_label_series(sales_df, "region"),
            revenue=sales_revenue,
        )
        .groupby("region", sort=False)["revenue"]
        .sum()
        .to_dict()
    )
    units_by_product = (
        sales_df.assign(
            product=_normalize_label_series(sales_df, "product"),
            units=sales_units,
        )
        .groupby("product", sort=False)["units"]
        .sum()
        .to_dict()
    )
    revenue_by_segment = (
        sales_df.assign(
            customer_segment=_normalize_label_series(sales_df, "customer_segment"),
            revenue=sales_revenue,
        )
        .groupby("customer_segment", sort=False)["revenue"]
        .sum()
        .to_dict()
    )

    status_counts = (
        orders_df.assign(order_status=_normalize_label_series(orders_df, "order_status"))
        .groupby("order_status", sort=False)
        .size()
        .to_dict()
    )

    campaign_spend = float(campaign_spend_series.sum())
    campaign_revenue = float(campaign_revenue_series.sum())
    campaign_conversions = int(campaign_conversion_series.sum())
    campaign_clicks = int(campaign_click_series.sum())
    avg_campaign_roas = campaign_revenue / campaign_spend if campaign_spend else 0

    spend_by_channel = (
        campaign_df.assign(
            channel=_normalize_label_series(campaign_df, "channel"),
            spend=campaign_spend_series,
        )
        .groupby("channel", sort=False)["spend"]
        .sum()
        .to_dict()
    )
    revenue_by_channel = (
        campaign_df.assign(
            channel=_normalize_label_series(campaign_df, "channel"),
            revenue=campaign_revenue_series,
        )
        .groupby("channel", sort=False)["revenue"]
        .sum()
        .to_dict()
    )
    spend_by_region = (
        campaign_df.assign(
            region=_normalize_label_series(campaign_df, "region"),
            spend=campaign_spend_series,
        )
        .groupby("region", sort=False)["spend"]
        .sum()
        .to_dict()
    )

    top_products_top_n = dashboard_config["charts"]["top_products_by_units"]["top_n"]
    include_others = dashboard_config["charts"]["top_products_by_units"]["include_others"]
    latest_sales_last_n_rows = dashboard_config["charts"]["latest_sales_orders"]["last_n_rows"]
    latest_campaigns_last_n_rows = dashboard_config["charts"]["latest_campaigns"]["last_n_rows"]
    sorted_channels = sorted(
        spend_by_channel.keys(),
        key=lambda channel_name: revenue_by_channel[channel_name],
        reverse=True,
    )
    if campaign_df.empty:
        latest_campaigns = []
    else:
        latest_campaigns = (
            campaign_df.sort_values("start_date", ascending=False)
            .head(latest_campaigns_last_n_rows)
            .to_dict("records")
        )
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
        "campaign_roas_trend": aggregate_campaign_roas_trend(
            campaign_rows,
            selected_trend,
            selected_start_date.isoformat() if selected_start_date else "",
            selected_end_date.isoformat() if selected_end_date else "",
        ),
        "campaign_spend_trend": aggregate_campaign_spend_trend(
            campaign_rows,
            selected_trend,
            selected_start_date.isoformat() if selected_start_date else "",
            selected_end_date.isoformat() if selected_end_date else "",
        ),
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
        "date_filter": {
            "start_date": selected_start_date.isoformat() if selected_start_date else "",
            "end_date": selected_end_date.isoformat() if selected_end_date else "",
            "region": selected_regions,
            "region_options": ["all", *available_regions],
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
