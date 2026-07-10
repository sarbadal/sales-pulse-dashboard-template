from __future__ import annotations

from collections import defaultdict
from datetime import timedelta

from src.constants import VALID_TREND_GRAIN
from src.utils.date_helpers import parse_iso_date
from src.utils.number_helpers import to_float


def aggregate_revenue_trend(sales_rows: list[dict[str, str]], granularity: str) -> dict[str, list]:
    period = granularity if granularity in VALID_TREND_GRAIN else "daily"
    revenue_by_period: dict[str, float] = defaultdict(float)
    bucket_by_period = {
        "weekly": lambda dt: dt - timedelta(days=dt.weekday()),  # Monday start.
        "monthly": lambda dt: dt.replace(day=1),
    }
    resolve_bucket = bucket_by_period.get(period, lambda dt: dt)

    for row in sales_rows:
        current_date = parse_iso_date(row.get("date", ""))
        if not current_date:
            continue

        bucket_date = resolve_bucket(current_date)
        revenue_by_period[bucket_date.isoformat()] += to_float(row.get("revenue", "0"))

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
        start_date = parse_iso_date(row.get("start_date", ""))
        end_date = parse_iso_date(row.get("end_date", ""))
        if not start_date or not end_date or end_date < start_date:
            continue

        total_spend = to_float(row.get("spend", "0"))
        total_revenue = to_float(row.get("revenue", "0"))
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
        start_date = parse_iso_date(row.get("start_date", ""))
        end_date = parse_iso_date(row.get("end_date", ""))
        if not start_date or not end_date or end_date < start_date:
            continue

        total_spend = to_float(row.get("spend", "0"))
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
