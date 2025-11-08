from flask import Flask

from config import get_config

from .db import create_schema, init_app as init_db


def create_app() -> Flask:
    """Application factory for the Flask API."""
    app = Flask(__name__)
    app.config.from_object(get_config())
    init_db(app)

    from .routes import api_bp

    app.register_blueprint(api_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "ok"}

    @app.cli.command("init-db")
    def init_db_command():
        """Create the database schema defined in app/schema.sql."""
        create_schema(app)
        print("Database schema created.")

    return app
