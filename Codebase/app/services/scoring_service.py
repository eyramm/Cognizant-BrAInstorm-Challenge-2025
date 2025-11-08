from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Sequence, Tuple

from ..db import get_connection

IngredientRow = Tuple[
    Optional[str],  # tag
    Optional[str],  # name
    Optional[Decimal],
    Optional[Decimal],
    Optional[Decimal],
    Optional[int],  # rank
    Optional[Decimal],
    Optional[str],  # confidence
]


class ScoringService:
    """Service for calculating sustainability scores."""

    NOVA_MULTIPLIERS = {
        1: 1.0,  # Unprocessed
        2: 1.1,  # Processed culinary ingredients
        3: 1.2,  # Processed foods
        4: 1.5,  # Ultra-processed
        None: 1.2,  # Default if NOVA unknown
    }

    @classmethod
    def calculate_raw_materials_score(cls, product_id: int) -> Dict[str, Any]:
        """
        Calculate raw materials score for a product (range: -15 to +10 points).
        """
        conn = get_connection()

        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT nova_group FROM products WHERE id = %s",
                (product_id,),
            )
            product_row = cursor.fetchone()

        if not product_row:
            return {
                "points": None,
                "error": "Product not found",
            }

        nova_group = product_row[0]

        with conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    i.tag,
                    i.name,
                    pi.percent_estimate,
                    pi.percent_min,
                    pi.percent_max,
                    pi.rank,
                    ief.kg_co2_per_kg,
                    ief.confidence
                FROM product_ingredients AS pi
                JOIN ingredients AS i ON i.id = pi.ingredient_id
                LEFT JOIN ingredient_emission_factors AS ief
                    ON ief.ingredient_tag = i.tag
                WHERE pi.product_id = %s
                ORDER BY pi.rank
                """,
                (product_id,),
            )
            ingredients: List[IngredientRow] = cursor.fetchall()

        return cls._calculate_ingredient_co2(ingredients, nova_group)

    @classmethod
    def _calculate_ingredient_co2(
        cls,
        ingredients: Sequence[IngredientRow],
        nova_group: Optional[int],
    ) -> Dict[str, Any]:
        """
        Calculate CO2 from ingredients with graceful degradation.
        """
        ingredient_count = len(ingredients)

        if ingredient_count == 0:
            return cls._fallback_nova_only(nova_group)

        has_percentages = any(row[2] is not None for row in ingredients)
        has_emission_factors = any(row[6] is not None for row in ingredients)

        if not has_emission_factors:
            return cls._fallback_no_emission_factors(nova_group)

        total_co2 = 0.0
        total_percent = 0.0
        ingredients_with_data = 0

        for (
            _tag,
            _name,
            percent_est,
            _percent_min,
            _percent_max,
            _rank,
            kg_co2,
            _confidence,
        ) in ingredients:
            if kg_co2 is None:
                continue

            if percent_est is not None:
                percent = float(percent_est)
            elif has_percentages:
                # Other ingredients include explicit percentages; skip this one
                continue
            else:
                percent = 100.0 / ingredient_count

            co2_contribution = (percent / 100.0) * float(kg_co2)
            total_co2 += co2_contribution
            total_percent += percent
            ingredients_with_data += 1

        nova_multiplier = cls.NOVA_MULTIPLIERS.get(nova_group, 1.2)
        final_co2 = total_co2 * nova_multiplier
        points = cls._co2_to_points(final_co2)

        coverage = (
            ingredients_with_data / ingredient_count if ingredient_count else 0.0
        )

        confidence = cls._determine_confidence(
            has_percentages=has_percentages,
            ingredient_coverage=coverage,
            nova_group=nova_group,
        )

        return {
            "points": points,
            "total_co2_kg": round(final_co2, 4),
            "breakdown": {
                "ingredient_co2": round(total_co2, 4),
                "nova_group": nova_group,
                "nova_multiplier": nova_multiplier,
                "final_co2": round(final_co2, 4),
            },
            "confidence": confidence,
            "data_quality": {
                "has_percentages": has_percentages,
                "has_emission_factors": has_emission_factors,
                "ingredient_coverage": round(coverage, 2),
                "total_percent_covered": round(total_percent, 1),
                "fallback_used": None
                if has_percentages and coverage > 0.8
                else "equal_distribution",
            },
        }

    @staticmethod
    def _co2_to_points(co2_kg: float) -> int:
        """
        Convert kg CO2 per kg product to score points (-15 to +10).
        """
        if co2_kg < 1.0:
            return 10
        if co2_kg < 2.0:
            return 5
        if co2_kg < 5.0:
            return 0
        if co2_kg < 10.0:
            return -5
        return -15

    @staticmethod
    def _determine_confidence(
        has_percentages: bool,
        ingredient_coverage: float,
        nova_group: Optional[int],
    ) -> str:
        """Determine confidence level of the score."""
        if has_percentages and ingredient_coverage >= 0.8:
            return "high"
        if ingredient_coverage >= 0.5:
            return "medium"
        return "low"

    @classmethod
    def _fallback_nova_only(cls, nova_group: Optional[int]) -> Dict[str, Any]:
        """
        Fallback when no ingredient data available.
        """
        nova_estimates = {
            1: 0.8,
            2: 1.5,
            3: 3.0,
            4: 5.0,
            None: 3.0,
        }

        estimated_co2 = nova_estimates.get(nova_group, 3.0)
        points = cls._co2_to_points(estimated_co2)

        return {
            "points": points,
            "total_co2_kg": estimated_co2,
            "breakdown": {
                "ingredient_co2": None,
                "nova_group": nova_group,
                "nova_multiplier": 1.0,
                "final_co2": estimated_co2,
            },
            "confidence": "low",
            "data_quality": {
                "has_percentages": False,
                "has_emission_factors": False,
                "ingredient_coverage": 0.0,
                "total_percent_covered": 0.0,
                "fallback_used": "nova_only_estimate",
            },
        }

    @classmethod
    def _fallback_no_emission_factors(
        cls, nova_group: Optional[int]
    ) -> Dict[str, Any]:
        """
        Fallback when ingredients exist but lack emission factors.
        """
        return cls._fallback_nova_only(nova_group)

    @classmethod
    def calculate_packaging_score(cls, product_id: int) -> Dict[str, Any]:
        """
        Calculate packaging score for a product (range: -15 to +10 points).

        Scoring is based on environmental impact of packaging materials:
        - Cardboard/Paper: 87/100 environmental score → +10 points
        - Aluminum: 68/100 → +5 points
        - Steel/Tin: 65/100 → +3 points
        - Glass: 51/100 → 0 points
        - PET Plastic: 28/100 → -8 points
        - HDPE Plastic: 26/100 → -10 points
        - Composite/Tetra: 25/100 → -12 points
        - Mixed Plastic: 23/100 → -15 points
        """
        conn = get_connection()

        with conn.cursor() as cursor:
            # Get all packaging materials for this product
            cursor.execute(
                """
                SELECT
                    pm.name,
                    pm.environmental_score,
                    pm.score_adjustment,
                    pm.recyclability_score,
                    pm.recycling_rate_pct,
                    pm.biodegradability_score,
                    pm.transport_impact_score,
                    pm.production_kg_co2_per_kg,
                    p.weight_percentage
                FROM packagings AS p
                JOIN packaging_materials AS pm ON pm.id = p.material_id
                WHERE p.product_id = %s
                """,
                (product_id,),
            )
            packaging_rows = cursor.fetchall()

        if not packaging_rows:
            return {
                "points": 0,
                "status": "no_packaging_data",
                "message": "No packaging information available",
                "confidence": "none",
            }

        # Calculate weighted average score based on weight percentages
        total_weighted_score = 0.0
        total_weight = 0.0
        total_co2 = 0.0
        materials_breakdown = []

        has_weights = any(row[8] is not None for row in packaging_rows)

        for row in packaging_rows:
            (
                name,
                env_score,
                score_adjustment,
                recyclability,
                recycling_rate,
                biodegradability,
                transport_impact,
                co2_per_kg,
                weight_pct,
            ) = row

            # If no weight percentages, assume equal distribution
            if weight_pct is not None:
                weight = float(weight_pct) / 100.0
            elif has_weights:
                # Skip materials without weights if others have them
                continue
            else:
                weight = 1.0 / len(packaging_rows)

            total_weighted_score += score_adjustment * weight
            total_weight += weight

            if co2_per_kg is not None:
                total_co2 += float(co2_per_kg) * weight

            materials_breakdown.append({
                "material": name,
                "environmental_score": env_score,
                "score_adjustment": score_adjustment,
                "weight_percentage": round(weight * 100, 1),
                "recyclability": recyclability,
                "recycling_rate": float(recycling_rate) if recycling_rate else None,
                "biodegradability": biodegradability,
                "transport_impact": transport_impact,
                "co2_kg_per_kg": float(co2_per_kg) if co2_per_kg else None,
            })

        # Calculate final score
        if total_weight > 0:
            final_score = round(total_weighted_score / total_weight)
        else:
            final_score = 0

        # Ensure score is within bounds
        final_score = max(-15, min(10, final_score))

        # Determine confidence
        if has_weights and total_weight >= 0.8:
            confidence = "high"
        elif total_weight >= 0.5:
            confidence = "medium"
        else:
            confidence = "low"

        return {
            "points": final_score,
            "total_co2_kg_per_kg": round(total_co2, 4) if total_co2 > 0 else None,
            "materials_breakdown": materials_breakdown,
            "confidence": confidence,
            "data_quality": {
                "has_weight_percentages": has_weights,
                "total_weight_covered": round(total_weight, 2),
                "material_count": len(packaging_rows),
            },
        }
