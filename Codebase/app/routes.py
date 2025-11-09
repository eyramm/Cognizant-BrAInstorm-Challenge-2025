from flask import Blueprint, current_app, jsonify, request
import asyncio

from .db import get_connection
from .services.open_food_facts import OpenFoodFactsService
from .services.product_storage import ProductStorageService
from .workflows.product_scan_workflow import execute_product_scan_workflow

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
    Get product information using the complete workflow:
    1. Check database
    2. Fetch from API if needed
    3. Update database
    4. Calculate scores
    5. Find similar products
    6. Make recommendations

    Query params:
        - sustainability_score=true: Return complete workflow results (scores, recommendations)
        - ingredients=true: Include ingredient health analysis
        - lat: User/store latitude (optional, defaults to Halifax, NS)
        - lon: User/store longitude (optional, defaults to Halifax, NS)
    """
    try:
        if not barcode.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid barcode format. Must contain only digits."
            }), 400

        # Check if sustainability score calculation requested
        calculate_sustainability = request.args.get('sustainability_score', 'false').lower() == 'true'
        analyze_ingredients = request.args.get('ingredients', 'false').lower() == 'true'

        if calculate_sustainability:
            # Get location parameters (default to Halifax, NS if not provided)
            lat = request.args.get('lat', type=float)
            lon = request.args.get('lon', type=float)

            # Execute complete workflow with scores and recommendations
            result = execute_product_scan_workflow(
                barcode,
                user_lat=lat,
                user_lon=lon,
                analyze_ingredients=analyze_ingredients
            )
            return jsonify(result)
        else:
            # Quick response - just product info
            conn = get_connection()

            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT p.id, p.upc, p.product_name, m.name as brand,
                              p.quantity, p.manufacturing_places,
                              c.name as primary_category,
                              p.image_url,
                              p.image_small_url
                       FROM products p
                       LEFT JOIN manufacturers m ON p.brand_id = m.id
                       LEFT JOIN product_categories pc ON p.id = pc.product_id AND pc.is_primary = TRUE
                       LEFT JOIN categories c ON pc.category_id = c.id
                       WHERE p.upc = %s OR p.upc = %s""",
                    (barcode, barcode.zfill(13))
                )
                existing_product = cursor.fetchone()

            if existing_product:
                response_data = {
                    "upc": existing_product[1],
                    "product_name": existing_product[2],
                    "brand": existing_product[3],
                    "quantity": existing_product[4],
                    "manufacturing_places": existing_product[5],
                    "primary_category": existing_product[6],
                    "image_url": existing_product[7],
                    "image_small_url": existing_product[8]
                }

                # Add ingredient analysis if requested
                if analyze_ingredients:
                    from .services.ingredient_analysis_service import IngredientAnalysisService
                    product_id = existing_product[0]
                    response_data["ingredients_analysis"] = IngredientAnalysisService.analyze_ingredients(product_id)

                return jsonify({
                    "status": "success",
                    "source": "database",
                    "data": response_data
                })

            # Not in database - fetch and save
            off_product = asyncio.run(OpenFoodFactsService.fetch_product(barcode))

            if not off_product:
                return jsonify({
                    "status": "not_found",
                    "message": f"Product with barcode {barcode} not found."
                }), 404

            try:
                ProductStorageService.save_product(conn, off_product)
            except Exception:
                conn.rollback()

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
                    "primary_category": product_info.get('primary_category'),
                    "image_url": product_info.get('image_front_url'),
                    "image_small_url": product_info.get('image_front_small_url')
                }
            })

    except Exception as exc:
        current_app.logger.exception(f"Error fetching product {barcode}")
        return jsonify({
            "status": "error",
            "message": "An error occurred while fetching product information."
        }), 500
