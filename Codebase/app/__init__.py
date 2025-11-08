from flask import Flask

from config import get_config


def create_app() -> Flask:
    """Application factory for the Flask API."""
    app = Flask(__name__)
    app.config.from_object(get_config())

    from .routes import api_bp

    app.register_blueprint(api_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "ok"}

    return app
