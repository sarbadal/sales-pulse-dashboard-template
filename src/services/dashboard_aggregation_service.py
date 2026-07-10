from __future__ import annotations

import pandas as pd

from src.constants import VALID_TREND_GRAIN


def _resolve_period(granularity: str) -> str:
    return granularity if granularity in VALID_TREND_GRAIN else "daily"


def _bucket_dates(date_series: pd.Series, period: str) -> pd.Series:
    if period == "weekly":
        return (date_series - pd.to_timedelta(date_series.dt.weekday, unit="D")).dt.normalize()
    if period == "monthly":
        return date_series.dt.to_period("M").dt.to_timestamp()
    return date_series.dt.normalize()


def _build_campaign_daily_distribution(campaign_rows: list[dict[str, str]]) -> pd.DataFrame:
    campaign_df = pd.DataFrame(campaign_rows)
    if campaign_df.empty:
        return pd.DataFrame(columns=["current_day", "daily_spend", "daily_revenue"])

    start_date = pd.to_datetime(campaign_df.get("start_date"), errors="coerce")
    end_date = pd.to_datetime(campaign_df.get("end_date"), errors="coerce")
    spend = pd.to_numeric(campaign_df.get("spend"), errors="coerce").fillna(0)
    revenue = pd.to_numeric(campaign_df.get("revenue"), errors="coerce").fillna(0)

    valid = start_date.notna() & end_date.notna() & (end_date >= start_date)
    if not valid.any():
        return pd.DataFrame(columns=["current_day", "daily_spend", "daily_revenue"])

    distributed_df = pd.DataFrame(
        {
            "start_date": start_date[valid],
            "end_date": end_date[valid],
            "spend": spend[valid],
            "revenue": revenue[valid],
        }
    )

    campaign_days = (distributed_df["end_date"] - distributed_df["start_date"]).dt.days + 1
    distributed_df = distributed_df[campaign_days > 0].copy()
    if distributed_df.empty:
        return pd.DataFrame(columns=["current_day", "daily_spend", "daily_revenue"])

    distributed_df["campaign_days"] = campaign_days[campaign_days > 0]
    distributed_df["daily_spend"] = distributed_df["spend"] / distributed_df["campaign_days"]
    distributed_df["daily_revenue"] = distributed_df["revenue"] / distributed_df["campaign_days"]
    distributed_df["current_day"] = distributed_df.apply(
        lambda row: pd.date_range(row["start_date"], row["end_date"], freq="D"),
        axis=1,
    )

    return distributed_df.explode("current_day")


def aggregate_revenue_trend(sales_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    """Aggregate sales revenue into daily, weekly, or monthly trend buckets."""
    period = _resolve_period(granularity)
    sales_df = pd.DataFrame(sales_rows)
    if sales_df.empty:
        return {"labels": [], "values": []}

    parsed_date = pd.to_datetime(sales_df.get("date"), errors="coerce")
    revenue = pd.to_numeric(sales_df.get("revenue"), errors="coerce").fillna(0)
    valid = parsed_date.notna()
    if not valid.any():
        return {"labels": [], "values": []}

    trend_df = pd.DataFrame(
        {
            "bucket_date": _bucket_dates(parsed_date[valid], period),
            "revenue": revenue[valid],
        }
    )
    grouped = (
        trend_df.groupby("bucket_date", as_index=False)["revenue"]
        .sum()
        .sort_values("bucket_date")
    )

    return {
        "labels": grouped["bucket_date"].dt.strftime("%Y-%m-%d").tolist(),
        "values": grouped["revenue"].round(2).tolist(),
    }


def aggregate_campaign_roas_trend(campaign_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    """Aggregate campaign ROAS over time using distributed daily spend and revenue."""
    period = _resolve_period(granularity)
    distributed_df = _build_campaign_daily_distribution(campaign_rows)
    if distributed_df.empty:
        return {"labels": [], "values": []}

    distributed_df["bucket_date"] = _bucket_dates(distributed_df["current_day"], period)
    grouped = (
        distributed_df.groupby("bucket_date", as_index=False)
        .agg(
            spend=("daily_spend", "sum"),
            revenue=("daily_revenue", "sum"),
        )
        .sort_values("bucket_date")
    )

    roas = (grouped["revenue"] / grouped["spend"]).where(grouped["spend"] != 0, 0).fillna(0)

    return {
        "labels": grouped["bucket_date"].dt.strftime("%Y-%m-%d").tolist(),
        "values": roas.round(2).tolist(),
    }


def aggregate_campaign_spend_trend(campaign_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    """Aggregate campaign spend over time by spreading spend across campaign dates."""
    period = _resolve_period(granularity)
    distributed_df = _build_campaign_daily_distribution(campaign_rows)
    if distributed_df.empty:
        return {"labels": [], "values": []}

    distributed_df["bucket_date"] = _bucket_dates(distributed_df["current_day"], period)
    grouped = (
        distributed_df.groupby("bucket_date", as_index=False)["daily_spend"]
        .sum()
        .sort_values("bucket_date")
    )

    return {
        "labels": grouped["bucket_date"].dt.strftime("%Y-%m-%d").tolist(),
        "values": grouped["daily_spend"].round(2).tolist(),
    }
