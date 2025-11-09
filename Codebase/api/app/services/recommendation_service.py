"""Service for product recommendations based on sustainability and health."""

import asyncio
from typing import Dict, Any, List, Optional
from flask import current_app

from ..db import get_connection
from .open_food_facts import OpenFoodFactsService
from .product_storage import ProductStorageService
from .scoring_service import ScoringService
from .ingredient_analysis_service import IngredientAnalysisService


class RecommendationService:
    """Service for finding and ranking product recommendations."""

    @classmethod
    def get_similar_products_from_db(cls, product_id: int, category: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Find similar products in local database by category.

        Args:
            product_id: Current product ID to exclude
            category: Primary category to match
            limit: Maximum number of products to return

        Returns:
            List of similar products with basic info
        """
        if not category:
            return []

        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """SELECT p.id, p.upc, p.product_name, m.name as brand,
                          c.name as category, p.image_small_url, p.price
                   FROM products p
                   LEFT JOIN manufacturers m ON p.brand_id = m.id
                   LEFT JOIN product_categories pc ON p.id = pc.product_id AND pc.is_primary = TRUE
                   LEFT JOIN categories c ON pc.category_id = c.id
                   WHERE c.name = %s
                     AND p.id != %s
                   LIMIT %s""",
                (category, product_id, limit)
            )
            results = cursor.fetchall()

        similar = []
        for row in results:
            similar.append({
                "id": row[0],
                "upc": row[1],
                "product_name": row[2],
                "brand": row[3],
                "category": row[4],
                "image_small_url": row[5],
                "price": float(row[6]) if row[6] is not None else None
            })

        return similar

    @classmethod
    async def fetch_and_save_similar_products(cls, category: str, exclude_upcs: List[str],
                                               needed: int = 10) -> List[Dict[str, Any]]:
        """
        Fetch similar products from Open Food Facts API and save to database.

        Args:
            category: Category to search
            exclude_upcs: List of UPCs to exclude (already in local DB)
            needed: Number of new products needed

        Returns:
            List of newly saved products with IDs
        """
        if not category:
            return []

        # Convert category name to tag format (e.g., "Canned Meats" -> "canned-meats")
        category_tag = category.lower().replace(' ', '-')

        current_app.logger.info(f"[Recommendations] Searching OFF API for category: {category_tag}")

        # Fetch from Open Food Facts
        off_products = await OpenFoodFactsService.search_products_by_category(
            category_tag,
            page_size=needed * 2  # Get more to account for duplicates
        )

        if not off_products:
            current_app.logger.info(f"[Recommendations] No products found in OFF API for {category_tag}")
            return []

        current_app.logger.info(f"[Recommendations] Found {len(off_products)} products from OFF API")

        # Save new products to database
        conn = get_connection()
        saved_products = []

        for off_product in off_products:
            # Skip if we already have this product
            upc = off_product.get('code')
            if not upc or upc in exclude_upcs:
                continue

            # Check if already in DB
            with conn.cursor() as cursor:
                cursor.execute("SELECT id FROM products WHERE upc = %s", (upc,))
                if cursor.fetchone():
                    continue

            # Save to database
            try:
                product_id = ProductStorageService.save_product(conn, off_product)
                current_app.logger.info(f"[Recommendations] Saved product {upc} with ID {product_id}")

                saved_products.append({
                    "id": product_id,
                    "upc": upc,
                    "product_name": off_product.get('product_name'),
                    "brand": off_product.get('brands'),
                    "category": category,
                    "image_small_url": off_product.get('image_front_small_url')
                })

                # Stop when we have enough
                if len(saved_products) >= needed:
                    break

            except Exception as e:
                current_app.logger.warning(f"[Recommendations] Failed to save product {upc}: {e}")
                continue

        current_app.logger.info(f"[Recommendations] Saved {len(saved_products)} new products to DB")
        return saved_products

    @classmethod
    def calculate_recommendation_score(cls, product_id: int, user_lat: Optional[float] = None,
                                       user_lon: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive recommendation score for a product.

        Uses cached transportation score from database for speed.

        Args:
            product_id: Product ID
            user_lat: User latitude (optional, uses default from config)
            user_lon: User longitude (optional, uses default from config)

        Returns:
            Dictionary with scores and ranking metrics
        """
        from ..db import get_connection

        # Calculate sustainability score
        raw_materials = ScoringService.calculate_raw_materials_score(product_id)
        raw_points = raw_materials.get("points", 0) if isinstance(raw_materials.get("points"), (int, float)) else 0

        packaging = ScoringService.calculate_packaging_score(product_id)
        packaging_points = packaging.get("points", 0) if isinstance(packaging.get("points"), (int, float)) else 0

        # Get cached transportation score from database (fast!)
        conn = get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT transportation_score FROM products WHERE id = %s", (product_id,))
            result = cursor.fetchone()
            transportation_points = result[0] if result and result[0] is not None else 0

        climate = ScoringService.calculate_climate_efficiency_score(product_id)
        climate_points = climate.get("points", 0) if isinstance(climate.get("points"), (int, float)) else 0

        # Calculate total sustainability score (0-100) with all 4 metrics
        total_points = raw_points + packaging_points + transportation_points + climate_points
        sustainability_score = max(0, min(100, 50 + total_points))

        # Calculate grade
        if sustainability_score >= 80:
            grade = "A"
        elif sustainability_score >= 60:
            grade = "B"
        elif sustainability_score >= 40:
            grade = "C"
        elif sustainability_score >= 20:
            grade = "D"
        else:
            grade = "E"

        # Get ingredient health analysis
        ingredients = IngredientAnalysisService.analyze_ingredients(product_id)
        harmful_count = ingredients.get("summary", {}).get("harmful", 0)
        caution_count = ingredients.get("summary", {}).get("caution", 0)

        # Calculate health penalty (reduce score for harmful ingredients)
        health_penalty = (harmful_count * 5) + (caution_count * 2)

        # Final recommendation score
        recommendation_score = max(0, sustainability_score - health_penalty)

        return {
            "sustainability_score": sustainability_score,
            "grade": grade,
            "harmful_ingredients": harmful_count,
            "caution_ingredients": caution_count,
            "health_penalty": health_penalty,
            "recommendation_score": recommendation_score
        }

    @classmethod
    async def get_recommendations(cls, product_id: int, category: str, current_score: float,
                                  user_lat: Optional[float] = None, user_lon: Optional[float] = None,
                                  min_count: int = 3) -> List[Dict[str, Any]]:
        """
        Get product recommendations using hybrid approach (local DB + OFF API).

        Args:
            product_id: Current product ID
            category: Product category
            current_score: Current product's recommendation score (to filter better products)
            user_lat: User latitude
            user_lon: User longitude
            min_count: Minimum number of recommendations to try to return (default 3)

        Returns:
            List of recommended products with scores and reasons
        """
        # Step 1: Get similar products from local database
        local_products = cls.get_similar_products_from_db(product_id, category, limit=20)
        current_app.logger.info(f"[Recommendations] Found {len(local_products)} similar products in local DB")

        # Step 2: If we don't have enough, fetch from Open Food Facts
        if len(local_products) < min_count:
            needed = min_count - len(local_products)
            exclude_upcs = [p["upc"] for p in local_products]

            new_products = await cls.fetch_and_save_similar_products(category, exclude_upcs, needed)
            local_products.extend(new_products)

        # Step 3: Calculate scores for all products (in parallel for speed)
        scored_products = []
        for product in local_products:
            try:
                scores = cls.calculate_recommendation_score(product["id"])

                # Only recommend products with better scores
                if scores["recommendation_score"] > current_score:
                    scored_products.append({
                        **product,
                        **scores
                    })
            except Exception as e:
                current_app.logger.warning(f"[Recommendations] Error scoring product {product['id']}: {e}")
                continue

        # Step 4: Sort by recommendation score (highest first)
        scored_products.sort(key=lambda x: x["recommendation_score"], reverse=True)

        # Step 5: Build recommendation response with reasons
        recommendations = []
        for product in scored_products[:3]:  # Top 3
            reason_parts = []

            # Determine primary reason
            score_diff = product["recommendation_score"] - current_score
            if score_diff >= 20:
                reason_parts.append("Significantly better sustainability score")
            elif score_diff >= 10:
                reason_parts.append("Better sustainability score")
            else:
                reason_parts.append("Slightly better sustainability score")

            # Add health reason if applicable
            if product["harmful_ingredients"] == 0:
                reason_parts.append("no harmful ingredients")

            recommendations.append({
                "product": {
                    "upc": product["upc"],
                    "product_name": product["product_name"],
                    "brand": product["brand"],
                    "category": product["category"],
                    "image_small_url": product["image_small_url"],
                    "price": product.get("price")
                },
                "sustainability_score": product["sustainability_score"],
                "grade": product["grade"],
                "harmful_ingredients": product["harmful_ingredients"],
                "reason": " - ".join(reason_parts),
                "score_improvement": round(score_diff, 1)
            })

        current_app.logger.info(f"[Recommendations] Returning {len(recommendations)} recommendations")
        return recommendations
