from __future__ import annotations

from src.app_factory import create_app


app = create_app()


# functions-framework --target=entry_point --debug
def entry_point(request):
    """Entry point for Google Cloud Function"""
    return app


if __name__ == "__main__":
    app.run(debug=True)
