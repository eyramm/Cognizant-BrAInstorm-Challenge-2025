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

        conn = get_connection()

        # Step 1: Check if product exists in our database
        # Note: UPC might have leading zeros, so we check both formats
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT p.id, p.upc, p.product_name, p.brand_id, m.name as brand,
                          p.quantity, p.serving_size, p.nova_group,
                          p.manufacturing_places, p.ingredients_text,
                          p.ecoscore_grade, p.ecoscore_score, p.nutriscore_grade,
                          p.completeness, p.has_palm_oil
                   FROM products p
                   LEFT JOIN manufacturers m ON p.brand_id = m.id
                   WHERE p.upc = %s OR p.upc = %s""",
                (barcode, barcode.zfill(13))  # Check both formats
            )
            existing_product = cursor.fetchone()
            current_app.logger.info(f"Database check for {barcode}: found={existing_product is not None}")

        if existing_product:
            # Product exists in database - return from local data
            current_app.logger.info(f"Product {barcode} found in database (ID: {existing_product[0]})")

            # Fetch additional data (categories, labels, nutriments)
            with conn.cursor() as cursor:
                # Get categories
                cursor.execute(
                    """SELECT c.name
                       FROM product_categories pc
                       JOIN categories c ON pc.category_id = c.id
                       WHERE pc.product_id = %s
                       ORDER BY pc.position""",
                    (existing_product[0],)
                )
                categories = [row[0] for row in cursor.fetchall()]

                # Get labels
                cursor.execute(
                    """SELECT l.name, l.icon
                       FROM product_labels pl
                       JOIN labels l ON pl.label_id = l.id
                       WHERE pl.product_id = %s""",
                    (existing_product[0],)
                )
                labels = [row[0] for row in cursor.fetchall()]

                # Get nutriments
                cursor.execute(
                    """SELECT calories_100g, protein_100g, fat_100g, carbs_100g,
                              sugars_100g, salt_100g, fiber_100g
                       FROM nutriments
                       WHERE product_id = %s""",
                    (existing_product[0],)
                )
                nutriments_row = cursor.fetchone()

            # Build response from database data
            product_info = {
                'database_id': existing_product[0],
                'upc': existing_product[1],
                'product_name': existing_product[2],
                'brand': existing_product[4],
                'quantity': existing_product[5],
                'serving_size': existing_product[6],
                'nova_group': existing_product[7],
                'manufacturing_places': existing_product[8],
                'ingredients_text': existing_product[9],
                'ecoscore': {
                    'grade': existing_product[10],
                    'score': existing_product[11],
                },
                'nutriscore_grade': existing_product[12],
                'data_completeness': existing_product[13],
                'has_palm_oil': existing_product[14],
                'all_categories': ', '.join(categories) if categories else None,
                'primary_category': categories[-1] if categories else None,
                'labels': labels,
                'nutrition': {
                    'calories_100g': nutriments_row[0] if nutriments_row else None,
                    'protein_100g': nutriments_row[1] if nutriments_row else None,
                    'fat_100g': nutriments_row[2] if nutriments_row else None,
                    'carbohydrates_100g': nutriments_row[3] if nutriments_row else None,
                    'sugars_100g': nutriments_row[4] if nutriments_row else None,
                    'salt_100g': nutriments_row[5] if nutriments_row else None,
                    'fiber_100g': nutriments_row[6] if nutriments_row else None,
                } if nutriments_row else None
            }

            return jsonify({
                "status": "success",
                "source": "database",
                "data": product_info
            })

        # Step 2: Product not in database - fetch from Open Food Facts
        current_app.logger.info(f"Product {barcode} not found in database, fetching from Open Food Facts")

        off_product = asyncio.run(
            OpenFoodFactsService.fetch_product(barcode)
        )

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
            product_id = None

        # Step 4: Extract and return basic info
        product_info = OpenFoodFactsService.extract_basic_info(off_product)
        product_info['database_id'] = product_id

        return jsonify({
            "status": "success",
            "source": "open_food_facts",
            "data": product_info,
            "saved_to_db": product_id is not None
        })

    except Exception as exc:
        current_app.logger.exception(f"Error fetching product {barcode}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching product information."
        }), 500
