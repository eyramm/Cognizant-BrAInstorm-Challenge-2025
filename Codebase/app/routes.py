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
    Get product information - checks database first, then fetches from Open Food Facts if needed
    Returns limited fields: brand, product_name, primary_category, quantity, upc, manufacturing_places
    """
    try:
        if not barcode.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid barcode format. Must contain only digits."
            }), 400

        conn = get_connection()

        # Step 1: Check if product exists in our database (check multiple UPC formats)
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT p.id, p.upc, p.product_name, m.name as brand,
                          p.quantity, p.manufacturing_places,
                          c.name as primary_category
                   FROM products p
                   LEFT JOIN manufacturers m ON p.brand_id = m.id
                   LEFT JOIN product_categories pc ON p.id = pc.product_id AND pc.is_primary = TRUE
                   LEFT JOIN categories c ON pc.category_id = c.id
                   WHERE p.upc = %s OR p.upc = %s""",
                (barcode, barcode.zfill(13))
            )
            existing_product = cursor.fetchone()

        if existing_product:
            # Product exists in database - return limited fields
            current_app.logger.info(f"Product {barcode} found in database")

            return jsonify({
                "status": "success",
                "source": "database",
                "data": {
                    "upc": existing_product[1],
                    "product_name": existing_product[2],
                    "brand": existing_product[3],
                    "quantity": existing_product[4],
                    "manufacturing_places": existing_product[5],
                    "primary_category": existing_product[6]
                }
            })

        # Step 2: Product not in database - fetch from Open Food Facts
        current_app.logger.info(f"Product {barcode} not found in database, fetching from Open Food Facts")

        off_product = asyncio.run(OpenFoodFactsService.fetch_product(barcode))

        if not off_product:
            return jsonify({
                "status": "not_found",
                "message": f"Product with barcode {barcode} not found in Open Food Facts database."
            }), 404

        # Step 3: Save to database
        try:
            product_id = ProductStorageService.save_product(conn, off_product)
            current_app.logger.info(f"Saved new product {barcode} with ID {product_id}")
        except Exception as db_exc:
            conn.rollback()
            current_app.logger.exception(f"Error saving product {barcode} to database")

        # Step 4: Extract limited info from OFF data
        product_info = OpenFoodFactsService.extract_basic_info(off_product)

        return jsonify({
            "status": "success",
            "source": "open_food_facts",
            "data": {
                "upc": product_info.get('upc'),
                "product_name": product_info.get('product_name'),
                "brand": product_info.get('brand'),
                "quantity": product_info.get('quantity'),
                "manufacturing_places": product_info.get('manufacturing_places'),
                "primary_category": product_info.get('primary_category')
            }
        })

    except Exception as exc:
        current_app.logger.exception(f"Error fetching product {barcode}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching product information."
        }), 500
