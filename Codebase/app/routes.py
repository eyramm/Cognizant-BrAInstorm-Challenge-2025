from flask import Blueprint, current_app, jsonify, request

from .db import get_connection

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/echo")
def echo():
    payload = request.args.get("message", "Hello from Flask API")
    return jsonify({"message": payload})


@api_bp.get("/db/ping")
def db_ping():
    try:
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT current_database(), NOW() AT TIME ZONE 'UTC'")
            db_name, utc_timestamp = cursor.fetchone()
        return jsonify(
            {
                "status": "ok",
                "database": db_name,
                "timestamp_utc": utc_timestamp.isoformat(),
            }
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        current_app.logger.exception("Database ping failed")
        return jsonify({"status": "error", "message": str(exc)}), 503
