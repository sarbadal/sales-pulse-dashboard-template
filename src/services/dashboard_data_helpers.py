from __future__ import annotations

from datetime import date

import pandas as pd

from src.services.dashboard_types import DataFrameTriplet, DateRange, RegionRawInput
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


def _normalize_date_range(start_date_raw: str | None, end_date_raw: str | None) -> DateRange:
    start_date = parse_iso_date((start_date_raw or "").strip())
    end_date = parse_iso_date((end_date_raw or "").strip())

    if start_date and end_date and start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date


def _resolve_data_date_bounds(sales_df: pd.DataFrame, orders_df: pd.DataFrame, campaign_df: pd.DataFrame) -> DateRange:
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


def _normalize_region_filter(region_raw: RegionRawInput, available_regions: list[str]) -> list[str]:
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


def _apply_region_filter(sales_df: pd.DataFrame, orders_df: pd.DataFrame, campaign_df: pd.DataFrame, selected_regions: list[str]) -> DataFrameTriplet:
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


def _build_date_mask(
    frame: pd.DataFrame,
    column_name: str,
    start_date: date | None,
    end_date: date | None,
) -> pd.Series:
    if frame.empty:
        return pd.Series([], index=frame.index, dtype="bool")

    if column_name not in frame.columns:
        return pd.Series(False, index=frame.index, dtype="bool")

    parsed_dates = pd.to_datetime(frame[column_name], errors="coerce")
    mask = parsed_dates.notna()
    if start_date:
        mask &= parsed_dates >= pd.Timestamp(start_date)
    if end_date:
        mask &= parsed_dates <= pd.Timestamp(end_date)
    return mask


def _filter_dataframes_by_date_range(
    sales_df: pd.DataFrame,
    orders_df: pd.DataFrame,
    campaign_df: pd.DataFrame,
    start_date: date | None,
    end_date: date | None,
) -> DataFrameTriplet:
    if not start_date and not end_date:
        return sales_df, orders_df, campaign_df

    sales_mask = _build_date_mask(sales_df, "date", start_date, end_date)
    order_mask = _build_date_mask(orders_df, "order_date", start_date, end_date)

    if campaign_df.empty:
        campaign_mask = pd.Series([], index=campaign_df.index, dtype="bool")
    else:
        campaign_start = pd.to_datetime(campaign_df.get("start_date"), errors="coerce")
        campaign_end = pd.to_datetime(campaign_df.get("end_date"), errors="coerce")
        campaign_mask = campaign_start.notna() & campaign_end.notna()
        if start_date:
            campaign_mask &= campaign_end >= pd.Timestamp(start_date)
        if end_date:
            campaign_mask &= campaign_start <= pd.Timestamp(end_date)

    filtered_sales_df = sales_df[sales_mask].copy()
    filtered_orders_df = orders_df[order_mask].copy()
    filtered_campaign_df = campaign_df[campaign_mask].copy()

    return filtered_sales_df, filtered_orders_df, filtered_campaign_df
