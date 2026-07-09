from __future__ import annotations

from flask import Blueprint, render_template, request

from src.services.sales_service import build_dashboard_data

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def dashboard() -> str:
    trend = request.args.get("trend", "daily").strip().lower()
    data = build_dashboard_data(trend)
    return render_template("index.html", data=data)
