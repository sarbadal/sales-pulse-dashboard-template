from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote

from flask import Flask, url_for

from src.routes.dashboard_routes import dashboard_bp

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "src" / "templates"),
        static_folder=str(BASE_DIR / "src" / "static"),
    )

    bucket_name = os.getenv("STATIC_BUCKET", "").strip().removeprefix("gs://")
    static_base_url = os.getenv("STATIC_BASE_URL", "").strip()
    if not static_base_url and bucket_name:
        static_base_url = f"https://storage.googleapis.com/{bucket_name}/static"

    def static_asset(filename: str) -> str:
        if static_base_url:
            return f"{static_base_url.rstrip('/')}/{quote(filename, safe='/')}"
        return url_for("static", filename=filename)

    app.jinja_env.globals["static_asset"] = static_asset
    app.register_blueprint(dashboard_bp)
    return app
