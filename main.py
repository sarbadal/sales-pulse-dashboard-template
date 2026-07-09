from __future__ import annotations

from pathlib import Path
from flask import Flask

from src.routes.dashboard_routes import dashboard_bp


BASE_DIR = Path(__file__).resolve().parent


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder=str(BASE_DIR / "src" / "templates"),
        static_folder=str(BASE_DIR / "src" / "static"),
    )
    app.register_blueprint(dashboard_bp)
    return app


app = create_app()


# functions-framework --target=entry_point --debug
def entry_point(request):
    """Entry point for Google Cloud Function"""
    return app


if __name__ == "__main__":
    app.run(debug=True)
