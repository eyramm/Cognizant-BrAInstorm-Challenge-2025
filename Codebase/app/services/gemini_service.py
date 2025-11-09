"""
Gemini AI Service
Handles generating AI-powered product summaries using Google's Gemini API
Caches summaries in database to reduce API calls
"""

import os
import json
from typing import Dict, Any, Optional
from google import genai
from flask import current_app
from ..db import get_connection


class GeminiService:
    """Service for interacting with Google Gemini AI"""

    _client = None

    @classmethod
    def _get_client(cls):
        """Initialize and return Gemini client (lazy loading)"""
        if cls._client is None:
            api_key = current_app.config.get('GEMINI_API_KEY')
            if not api_key or api_key == 'your-api-key-here':
                raise ValueError("GEMINI_API_KEY not configured. Please add your API key to .env file.")

            cls._client = genai.Client(api_key=api_key)

        return cls._client

    @classmethod
    def get_or_generate_summary(cls, product_id: int, product_data: Dict[str, Any]) -> Optional[str]:
        """
        Get cached summary from database or generate new one using Gemini AI.

        Args:
            product_id: Product ID to check for cached summary
            product_data: Complete product data for generating new summary

        Returns:
            AI-generated summary string or None if generation fails
        """
        # Step 1: Check if summary exists in database
        cached_summary = cls._get_cached_summary(product_id)
        if cached_summary:
            current_app.logger.info(f"[Gemini] Using cached summary for product {product_id}")
            return cached_summary

        # Step 2: Generate new summary
        current_app.logger.info(f"[Gemini] Generating new summary for product {product_id}")
        summary = cls._generate_new_summary(product_data)

        # Step 3: Save to database if successful
        if summary:
            cls._save_summary(product_id, summary)

        return summary

    @classmethod
    def _get_cached_summary(cls, product_id: int) -> Optional[str]:
        """
        Retrieve cached summary from database.

        Args:
            product_id: Product ID

        Returns:
            Cached summary text or None if not found
        """
        try:
            conn = get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """SELECT summary FROM product_summaries
                       WHERE product_id = %s""",
                    (product_id,)
                )
                result = cursor.fetchone()
                return result[0] if result else None

        except Exception as e:
            current_app.logger.warning(f"[Gemini] Error fetching cached summary: {e}")
            return None

    @classmethod
    def _save_summary(cls, product_id: int, summary: str) -> bool:
        """
        Save generated summary to database.

        Args:
            product_id: Product ID
            summary: AI-generated summary text

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            conn = get_connection()
            model_name = current_app.config.get('GEMINI_MODEL', 'gemini-1.5-flash')

            with conn.cursor() as cursor:
                cursor.execute(
                    """INSERT INTO product_summaries (product_id, summary, ai_model)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (product_id)
                       DO UPDATE SET
                           summary = EXCLUDED.summary,
                           ai_model = EXCLUDED.ai_model,
                           summary_version = product_summaries.summary_version + 1,
                           updated_at = NOW()""",
                    (product_id, summary, model_name)
                )
                conn.commit()
                current_app.logger.info(f"[Gemini] Saved summary for product {product_id}")
                return True

        except Exception as e:
            current_app.logger.exception(f"[Gemini] Error saving summary: {e}")
            return False

    @classmethod
    def _generate_new_summary(cls, product_data: Dict[str, Any]) -> Optional[str]:
        """
        Generate a new AI summary using Gemini API.

        Args:
            product_data: Complete product data

        Returns:
            AI-generated summary string or None if generation fails
        """
        try:
            client = cls._get_client()
            model_name = current_app.config.get('GEMINI_MODEL', 'gemini-2.0-flash-exp')

            # Build the prompt
            prompt = cls._build_summary_prompt(product_data)

            # Generate summary using new SDK
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )

            if response and response.text:
                return response.text
            else:
                current_app.logger.warning("[Gemini] No text in response")
                return None

        except ValueError as e:
            current_app.logger.error(f"[Gemini] Configuration error: {e}")
            return None
        except Exception as e:
            current_app.logger.exception(f"[Gemini] Error generating summary: {e}")
            return None

    @classmethod
    def _build_summary_prompt(cls, data: Dict[str, Any]) -> str:
        """
        Build a comprehensive prompt for Gemini to generate product insights.

        Args:
            data: Product data with scores, recommendations, and ingredients

        Returns:
            Formatted prompt string
        """
        product = data.get('product', {})
        scores = data.get('sustainability_scores', {})
        recommendations = data.get('recommendations', [])
        ingredients = data.get('ingredients_analysis', {})

        # Build prompt sections
        prompt_parts = [
            "You are an expert sustainability and nutrition analyst. Analyze this product and provide a concise, insightful summary.",
            "",
            "# PRODUCT INFORMATION",
            f"Product: {product.get('product_name', 'Unknown')}",
            f"Brand: {product.get('brand', 'Unknown')}",
            f"Category: {product.get('primary_category', 'Unknown')}",
        ]

        # Add price if available
        if product.get('price'):
            prompt_parts.append(f"Price: ${product.get('price')}")

        # Add sustainability scores
        if scores:
            prompt_parts.extend([
                "",
                "# SUSTAINABILITY ANALYSIS",
                f"Overall Score: {scores.get('total_score', 'N/A')}/100 (Grade {scores.get('grade', 'N/A')})",
            ])

            metrics = scores.get('metrics', {})

            # Raw materials
            if 'raw_materials' in metrics:
                rm = metrics['raw_materials']
                prompt_parts.append(f"- Raw Materials: {rm.get('score', 0)} points (CO2: {rm.get('co2_kg_per_kg', 'N/A')} kg/kg)")

            # Packaging
            if 'packaging' in metrics:
                pkg = metrics['packaging']
                prompt_parts.append(f"- Packaging: {pkg.get('score', 0)} points")

            # Transportation
            if 'transportation' in metrics:
                trans = metrics['transportation']
                prompt_parts.append(f"- Transportation: {trans.get('score', 0)} points ({trans.get('distance_km', 'N/A')} km)")

            # Climate efficiency
            if 'climate_efficiency' in metrics:
                climate = metrics['climate_efficiency']
                if climate.get('data_available'):
                    prompt_parts.append(
                        f"- Climate Efficiency: {climate.get('score', 0)} points "
                        f"({climate.get('co2_per_100_calories', 'N/A')} kg CO2/100 cal, "
                        f"Rating: {climate.get('efficiency_rating', 'N/A')})"
                    )

        # Add ingredient analysis
        if ingredients and ingredients.get('data_available'):
            summary = ingredients.get('summary', {})
            prompt_parts.extend([
                "",
                "# INGREDIENT HEALTH ANALYSIS",
                f"Total Ingredients: {summary.get('total', 0)}",
                f"- Good: {summary.get('good', 0)}",
                f"- Caution: {summary.get('caution', 0)}",
                f"- Harmful: {summary.get('harmful', 0)}",
            ])

            # List harmful ingredients if any
            harmful = [ing for ing in ingredients.get('ingredients', [])
                      if ing.get('health_impact') == 'harmful']
            if harmful:
                prompt_parts.append("Harmful ingredients:")
                for ing in harmful[:3]:  # Top 3
                    prompt_parts.append(f"  - {ing.get('name')}: {ing.get('reason', 'Health concern')}")

        # Add recommendations
        if recommendations:
            prompt_parts.extend([
                "",
                "# BETTER ALTERNATIVES",
                f"Found {len(recommendations)} better alternatives:",
            ])

            for i, rec in enumerate(recommendations[:3], 1):
                rec_product = rec.get('product', {})
                prompt_parts.extend([
                    f"{i}. {rec_product.get('product_name')} by {rec_product.get('brand', 'Unknown')}",
                    f"   - Score: {rec.get('sustainability_score')}/100 (Grade {rec.get('grade')})",
                    f"   - Improvement: +{rec.get('score_improvement')} points",
                    f"   - Why: {rec.get('reason')}",
                ])
                if rec_product.get('price'):
                    prompt_parts.append(f"   - Price: ${rec_product.get('price')}")

        # Add instruction for summary
        prompt_parts.extend([
            "",
            "# YOUR TASK",
            "Provide a concise 3-4 paragraph summary covering:",
            "1. Overall sustainability assessment (is this a good or bad choice environmentally?)",
            "2. Key health considerations from ingredients (if any concerns exist)",
            "3. Recommended alternatives and why they're better",
            "4. Final recommendation - should the user choose this product or switch?",
            "",
            "Be direct, actionable, and honest. Use simple language. Focus on insights, not just repeating data.",
        ])

        return "\n".join(prompt_parts)
