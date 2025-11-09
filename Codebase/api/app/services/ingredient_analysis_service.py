"""Service for analyzing product ingredients and health classification."""

from typing import Any, Dict, List
from ..db import get_connection


class IngredientAnalysisService:
    """Service for analyzing product ingredients and their health impacts."""

    @classmethod
    def analyze_ingredients(cls, product_id: int) -> Dict[str, Any]:
        """
        Analyze all ingredients in a product and classify by health impact.

        Args:
            product_id: Product ID

        Returns:
            Dictionary with summary and detailed ingredient analysis
        """
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    i.name,
                    i.tag,
                    i.health_classification,
                    i.health_concerns,
                    i.is_additive,
                    i.additive_code,
                    i.vegan_status,
                    i.vegetarian_status,
                    i.is_from_palm_oil,
                    pi.percent_estimate,
                    pi.rank
                FROM product_ingredients AS pi
                JOIN ingredients AS i ON i.id = pi.ingredient_id
                WHERE pi.product_id = %s
                ORDER BY pi.rank
                """,
                (product_id,),
            )
            ingredient_rows = cursor.fetchall()

        if not ingredient_rows:
            return {
                "data_available": False,
                "summary": {
                    "total": 0,
                    "good": 0,
                    "caution": 0,
                    "harmful": 0
                },
                "ingredients": []
            }

        # Count classifications
        good_count = 0
        caution_count = 0
        harmful_count = 0
        ingredients_list = []

        for row in ingredient_rows:
            (
                name,
                tag,
                health_classification,
                health_concerns,
                is_additive,
                additive_code,
                vegan_status,
                vegetarian_status,
                is_from_palm_oil,
                percent_estimate,
                rank
            ) = row

            # Default to 'good' if no classification
            classification = health_classification or 'good'

            # Count by classification
            if classification == 'good':
                good_count += 1
            elif classification == 'caution':
                caution_count += 1
            elif classification == 'harmful':
                harmful_count += 1

            # Build ingredient data
            ingredient_data = {
                "name": name,
                "classification": classification,
                "rank": rank
            }

            # Add optional fields
            if percent_estimate:
                ingredient_data["percent"] = float(percent_estimate)

            if classification in ['caution', 'harmful'] and health_concerns:
                ingredient_data["health_concerns"] = health_concerns

            if is_additive and additive_code:
                ingredient_data["additive_code"] = additive_code

            if is_from_palm_oil:
                ingredient_data["contains_palm_oil"] = True

            if vegan_status:
                ingredient_data["vegan"] = vegan_status

            if vegetarian_status:
                ingredient_data["vegetarian"] = vegetarian_status

            ingredients_list.append(ingredient_data)

        return {
            "data_available": True,
            "summary": {
                "total": len(ingredient_rows),
                "good": good_count,
                "caution": caution_count,
                "harmful": harmful_count
            },
            "ingredients": ingredients_list
        }
