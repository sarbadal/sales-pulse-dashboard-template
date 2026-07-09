from __future__ import annotations

from flask import Flask

from routes.dashboard_routes import dashboard_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.register_blueprint(dashboard_bp)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
