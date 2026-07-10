from __future__ import annotations

from flask import Blueprint, redirect, render_template, request, url_for

from src.services.sales_service import (
    build_dashboard_data,
    load_dashboard_config,
    set_active_dashboard_option_overrides,
)

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard() -> str:
    trend = request.args.get("trend", "daily").strip().lower()
    data = build_dashboard_data(trend)
    return render_template("index.html", data=data)


@dashboard_bp.route("/config", methods=["GET", "POST"])
def config_selector() -> str:
    if request.method == "POST":
        action = request.form.get("action", "save_active_options").strip()
        if action == "save_active_options":
            overrides_payload = {
                "branding": {
                    "dashboard_title": request.form.get("dashboard_title", "").strip(),
                    "dashboard_title_color": request.form.get("dashboard_title_color", "").strip(),
                },
                "charts": {
                    "revenue_trend": {
                        "style": request.form.get("revenue_trend_style", "").strip(),
                    },
                    "revenue_by_region": {
                        "type": request.form.get("revenue_by_region_type", "").strip(),
                    },
                    "revenue_by_segment": {
                        "type": request.form.get("revenue_by_segment_type", "").strip(),
                    },
                    "order_status": {
                        "type": request.form.get("order_status_type", "").strip(),
                    },
                    "top_products_by_units": {
                        "top_n": request.form.get("top_products_top_n", "").strip(),
                        "color": request.form.get("top_products_color", "").strip(),
                        "include_others": request.form.get("top_products_include_others", "").strip(),
                    },
                    "campaign_channel_performance": {
                        "mode": request.form.get("campaign_channel_mode", "").strip(),
                        "split_spend_type": request.form.get("split_spend_type", "").strip(),
                        "split_revenue_type": request.form.get("split_revenue_type", "").strip(),
                    },
                    "latest_sales_orders": {
                        "show_table": request.form.get("show_latest_sales_table", "").strip(),
                        "last_n_rows": request.form.get("latest_sales_last_n_rows", "").strip(),
                    },
                    "latest_campaigns": {
                        "show_table": request.form.get("show_latest_campaigns_table", "").strip(),
                        "last_n_rows": request.form.get("latest_campaigns_last_n_rows", "").strip(),
                    },
                }
            }
            if set_active_dashboard_option_overrides(overrides_payload):
                return redirect(url_for("dashboard.config_selector", status="options_saved"))
            return redirect(url_for("dashboard.config_selector", status="options_invalid"))

        return redirect(url_for("dashboard.config_selector", status="options_invalid"))

    active_config = load_dashboard_config()
    status = request.args.get("status", "").strip().lower()
    return render_template(
        "config_selector.html",
        active_config=active_config,
        status=status,
    )
