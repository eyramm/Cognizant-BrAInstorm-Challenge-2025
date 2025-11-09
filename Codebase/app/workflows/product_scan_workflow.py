"""
Product Scan Workflow
Orchestrates the complete flow when a user scans a product QR/barcode
"""

import asyncio
from typing import Dict, Any, Optional
from flask import current_app

from ..db import get_connection
from ..services.open_food_facts import OpenFoodFactsService
from ..services.product_storage import ProductStorageService


class ProductScanWorkflow:
    """
    Workflow for handling product scans

    Steps:
    1. Check internal database (default)
    2. If not found, fetch from external API (Open Food Facts)
    3. Update database with fetched data
    4. Calculate sustainability scores
    5. Find similar products
    6. Make recommendations
    """

    def __init__(self, barcode: str, user_lat: Optional[float] = None, user_lon: Optional[float] = None):
        from flask import current_app

        self.barcode = barcode
        self.product_id = None
        self.product_data = None
        self.source = None
        self.scores = None
        self.similar_products = []
        self.recommendations = []
        # Default to configured store location if coordinates not provided
        self.user_lat = user_lat if user_lat is not None else current_app.config['DEFAULT_STORE_LAT']
        self.user_lon = user_lon if user_lon is not None else current_app.config['DEFAULT_STORE_LON']

    def execute(self) -> Dict[str, Any]:
        """
        Execute the complete workflow
        Returns complete product information with scores and recommendations
        """
        try:
            # Step 1: Check internal database
            current_app.logger.info(f"[Workflow] Step 1: Checking database for {self.barcode}")
            self.product_data = self._check_database()

            if not self.product_data:
                # Step 2: Fetch from external API
                current_app.logger.info(f"[Workflow] Step 2: Fetching from Open Food Facts")
                off_data = self._fetch_from_api()

                if not off_data:
                    return {
                        "status": "not_found",
                        "message": f"Product {self.barcode} not found"
                    }

                # Step 3: Update database
                current_app.logger.info(f"[Workflow] Step 3: Saving to database")
                self.product_id = self._save_to_database(off_data)

                # Fetch the saved data
                self.product_data = self._check_database()
                self.source = "open_food_facts"
            else:
                self.source = "database"

            # Step 4: Calculate sustainability scores
            current_app.logger.info(f"[Workflow] Step 4: Calculating sustainability scores")
            self.scores = self._calculate_scores()

            # Step 5: Find similar products
            current_app.logger.info(f"[Workflow] Step 5: Finding similar products")
            self.similar_products = self._find_similar_products()

            # Step 6: Make recommendations
            current_app.logger.info(f"[Workflow] Step 6: Generating recommendations")
            self.recommendations = self._make_recommendations()

            # Return complete response
            return {
                "status": "success",
                "source": self.source,
                "data": {
                    "product": self.product_data,
                    "sustainability_scores": self.scores,
                    "similar_products": self.similar_products,
                    "recommendations": self.recommendations
                }
            }

        except Exception as exc:
            current_app.logger.exception(f"[Workflow] Error in workflow for {self.barcode}")
            return {
                "status": "error",
                "message": "An error occurred processing the product"
            }

    def _check_database(self) -> Optional[Dict[str, Any]]:
        """
        Step 1: Check if product exists in internal database
        Returns product data if found, None otherwise
        """
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT p.id, p.upc, p.product_name, m.name as brand,
                          p.quantity, p.manufacturing_places,
                          c.name as primary_category,
                          p.nova_group, p.ecoscore_grade, p.ecoscore_score
                   FROM products p
                   LEFT JOIN manufacturers m ON p.brand_id = m.id
                   LEFT JOIN product_categories pc ON p.id = pc.product_id AND pc.is_primary = TRUE
                   LEFT JOIN categories c ON pc.category_id = c.id
                   WHERE p.upc = %s OR p.upc = %s""",
                (self.barcode, self.barcode.zfill(13))
            )
            result = cursor.fetchone()

        if result:
            self.product_id = result[0]
            return {
                "id": result[0],
                "upc": result[1],
                "product_name": result[2],
                "brand": result[3],
                "quantity": result[4],
                "manufacturing_places": result[5],
                "primary_category": result[6],
                "nova_group": result[7],
                "ecoscore_grade": result[8],
                "ecoscore_score": result[9]
            }

        return None

    def _fetch_from_api(self) -> Optional[Dict[str, Any]]:
        """
        Step 2: Fetch product from Open Food Facts API
        Returns raw OFF data if found, None otherwise
        """
        off_product = asyncio.run(
            OpenFoodFactsService.fetch_product(self.barcode)
        )
        return off_product

    def _save_to_database(self, off_data: Dict[str, Any]) -> Optional[int]:
        """
        Step 3: Save fetched product data to database
        Returns product ID if saved successfully
        """
        try:
            conn = get_connection()
            product_id = ProductStorageService.save_product(conn, off_data)
            current_app.logger.info(f"[Workflow] Saved product {self.barcode} with ID {product_id}")
            return product_id
        except Exception as exc:
            current_app.logger.exception(f"[Workflow] Error saving product {self.barcode}")
            return None

    def _calculate_scores(self) -> Dict[str, Any]:
        """
        Step 4: Calculate sustainability scores for the product.
        """
        if not self.product_id:
            return {}

        from ..services.scoring_service import ScoringService

        # Calculate raw materials score
        raw_materials = ScoringService.calculate_raw_materials_score(self.product_id)
        raw_points = raw_materials.get("points")
        raw_points_value = raw_points if isinstance(raw_points, (int, float)) else 0

        # Calculate packaging score
        packaging = ScoringService.calculate_packaging_score(self.product_id)
        packaging_points = packaging.get("points")
        packaging_points_value = packaging_points if isinstance(packaging_points, (int, float)) else 0

        # Calculate transportation score with user location
        transportation = ScoringService.calculate_transportation_score(
            self.product_id,
            user_lat=self.user_lat,
            user_lon=self.user_lon
        )
        transportation_points = transportation.get("points")
        transportation_points_value = transportation_points if isinstance(transportation_points, (int, float)) else 0

        # Calculate climate efficiency score
        climate_efficiency = ScoringService.calculate_climate_efficiency_score(self.product_id)
        climate_points = climate_efficiency.get("points")
        climate_points_value = climate_points if isinstance(climate_points, (int, float)) else 0

        # Calculate total points from all implemented metrics (4 metrics)
        total_points = raw_points_value + packaging_points_value + transportation_points_value + climate_points_value
        final_score = max(0, min(100, 50 + total_points))

        if final_score >= 80:
            grade = "A"
        elif final_score >= 60:
            grade = "B"
        elif final_score >= 40:
            grade = "C"
        elif final_score >= 20:
            grade = "D"
        else:
            grade = "E"

        # Build clean response with only implemented metrics
        scores = {
            "total_score": final_score,
            "grade": grade,
            "metrics": {}
        }

        # Only include raw materials if implemented
        if raw_points is not None and raw_materials.get("status") != "not_implemented":
            scores["metrics"]["raw_materials"] = {
                "score": raw_points,
                "co2_kg_per_kg": raw_materials.get("total_co2_kg"),
                "confidence": raw_materials.get("confidence")
            }

        # Only include packaging if implemented
        if packaging_points is not None and packaging.get("status") != "no_packaging_data":
            scores["metrics"]["packaging"] = {
                "score": packaging_points,
                "co2_kg_per_kg": packaging.get("total_co2_kg_per_kg"),
                "confidence": packaging.get("confidence")
            }

        # Only include transportation if implemented
        if transportation_points is not None and transportation.get("status") not in ["no_location_data", "geocoding_failed"]:
            scores["metrics"]["transportation"] = {
                "score": transportation_points,
                "distance_km": transportation.get("distance_km"),
                "transport_mode": transportation.get("transport_mode"),
                "co2_kg": transportation.get("co2_kg"),
                "confidence": transportation.get("confidence")
            }

        # Always include climate efficiency (will show data_available status)
        climate_metric = {
            "score": climate_points,
            "data_available": climate_efficiency.get("data_available", False),
            "confidence": climate_efficiency.get("confidence", "none")
        }

        # Add detailed metrics only if data is available
        if climate_efficiency.get("data_available"):
            climate_metric.update({
                "co2_per_100_calories": climate_efficiency.get("co2_per_100_calories"),
                "calories_100g": climate_efficiency.get("calories_100g"),
                "efficiency_rating": climate_efficiency.get("efficiency_rating"),
            })
            # Optional: include protein efficiency if available
            if climate_efficiency.get("co2_per_100g_protein") is not None:
                climate_metric["co2_per_100g_protein"] = climate_efficiency.get("co2_per_100g_protein")
                climate_metric["protein_100g"] = climate_efficiency.get("protein_100g")

        scores["metrics"]["climate_efficiency"] = climate_metric

        return scores

    def _find_similar_products(self) -> list:
        """
        Step 5: Find similar products based on category and brand
        Returns list of similar products
        """
        if not self.product_id or not self.product_data:
            return []

        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                # Find products in same category, different brand
                cursor.execute(
                    """SELECT p.id, p.upc, p.product_name, m.name as brand,
                              c.name as category
                       FROM products p
                       LEFT JOIN manufacturers m ON p.brand_id = m.id
                       LEFT JOIN product_categories pc ON p.id = pc.product_id AND pc.is_primary = TRUE
                       LEFT JOIN categories c ON pc.category_id = c.id
                       WHERE c.name = %s
                         AND p.id != %s
                       LIMIT 5""",
                    (self.product_data.get('primary_category'), self.product_id)
                )
                results = cursor.fetchall()

            similar = []
            for row in results:
                similar.append({
                    "id": row[0],
                    "upc": row[1],
                    "product_name": row[2],
                    "brand": row[3],
                    "category": row[4]
                })

            return similar

        except Exception as exc:
            current_app.logger.exception(f"[Workflow] Error finding similar products")
            return []

    def _make_recommendations(self) -> list:
        """
        Step 6: Generate recommendations based on sustainability scores
        Returns list of recommended alternatives
        """
        if not self.similar_products:
            return []

        # TODO: Implement actual recommendation logic based on scores
        # For now, just return similar products as recommendations
        recommendations = []
        for product in self.similar_products[:3]:
            recommendations.append({
                "product": product,
                "reason": "Similar product in same category",
                "sustainability_score": None  # TODO: Add actual scores
            })

        return recommendations


def execute_product_scan_workflow(
    barcode: str,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None
) -> Dict[str, Any]:
    """
    Convenience function to execute the product scan workflow

    Args:
        barcode: Product UPC/barcode
        user_lat: User/store latitude (optional, defaults to Halifax, NS)
        user_lon: User/store longitude (optional, defaults to Halifax, NS)

    Returns:
        Complete workflow result with product data, scores, and recommendations
    """
    workflow = ProductScanWorkflow(barcode, user_lat=user_lat, user_lon=user_lon)
    return workflow.execute()
