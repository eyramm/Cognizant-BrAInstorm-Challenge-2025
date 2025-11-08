from flask import Blueprint, current_app, jsonify, request
import asyncio

from .db import get_connection
from .services.open_food_facts import OpenFoodFactsService
from .services.product_storage import ProductStorageService

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


@api_bp.get("/products/<barcode>")
def get_product(barcode: str):
    """
    Get basic product information from Open Food Facts and save to database

    Args:
        barcode: Product UPC/barcode (e.g., 64100238220)

    Returns:
        JSON with basic product information

    Example:
        GET /api/products/64100238220
    """
    try:
        # Validate barcode format (basic check)
        if not barcode.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid barcode format. Must contain only digits."
            }), 400

        # Fetch raw product data from Open Food Facts
        off_product = asyncio.run(
            OpenFoodFactsService.fetch_product(barcode)
        )

        if not off_product:
            return jsonify({
                "status": "not_found",
                "message": f"Product with barcode {barcode} not found in Open Food Facts database."
            }), 404

        # Save to database
        conn = get_connection()
        try:
            product_id = ProductStorageService.save_product(conn, off_product)
            current_app.logger.info(f"Saved product {barcode} with ID {product_id}")
        except Exception as db_exc:
            conn.rollback()
            current_app.logger.exception(f"Error saving product {barcode} to database")
            # Continue to return data even if save fails
            product_id = None

        # Extract basic info for response
        product_info = OpenFoodFactsService.extract_basic_info(off_product)
        product_info['database_id'] = product_id

        return jsonify({
            "status": "success",
            "data": product_info,
            "saved_to_db": product_id is not None
        })

    except Exception as exc:
        current_app.logger.exception(f"Error fetching product {barcode}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching product information."
        }), 500
