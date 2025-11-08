"""
Open Food Facts API Service
Handles fetching and parsing product data from Open Food Facts API
"""

import aiohttp
import os
from typing import Optional, Dict, Any, List


class OpenFoodFactsService:
    """Service for interacting with Open Food Facts API"""

    @staticmethod
    def get_base_url() -> str:
        """Get base URL from environment or use default"""
        return os.getenv('OFF_BASE_URL', 'https://world.openfoodfacts.org/api/v2/product')

    @staticmethod
    def get_timeout() -> int:
        """Get API timeout from environment or use default"""
        return int(os.getenv('OFF_API_TIMEOUT', '10'))

    # Fields we need from the API (optimized query)
    REQUIRED_FIELDS = [
        'code',
        'product_name',
        'brands',
        'quantity',
        'serving_size',
        'categories',
        'categories_tags',
        'food_groups_tags',
        'nova_group',
        'ingredients',           # Structured ingredients array with percentages
        'ingredients_text',
        'ingredients_tags',
        'allergens_tags',
        'ingredients_from_palm_oil_tags',
        'nutriments',
        'manufacturing_places',
        'origins',
        'countries_tags',
        'packaging',
        'packaging_tags',
        'packagings',
        'labels',
        'labels_tags',
        'ecoscore_grade',
        'ecoscore_score',
        'ecoscore_data',
        'nutriscore_grade',
        'completeness',
        'data_quality_tags',
        'image_url',
        'image_front_url',
        'image_front_small_url',
    ]

    @classmethod
    async def fetch_product(cls, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Fetch product data from Open Food Facts API

        Args:
            barcode: Product UPC/barcode

        Returns:
            Product data dict or None if not found
        """
        base_url = cls.get_base_url()
        url = f"{base_url}/{barcode}.json"
        params = {'fields': ','.join(cls.REQUIRED_FIELDS)}

        try:
            timeout = cls.get_timeout()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()

                    # Check if product was found
                    if data.get('status') != 1:
                        return None

                    return data.get('product')

        except aiohttp.ClientError as e:
            # Log error but don't crash
            print(f"Error fetching product {barcode}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching product {barcode}: {e}")
            return None

    @classmethod
    def extract_basic_info(cls, off_product: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic product information for display

        Args:
            off_product: Raw product data from OFF API

        Returns:
            Structured basic product info
        """
        if not off_product:
            return {}

        # Helper to safely get nested values
        def safe_get(data: dict, *keys, default=None):
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key)
                else:
                    return default
                if data is None:
                    return default
            return data

        # Extract nutriments
        nutriments = off_product.get('nutriments', {})

        # Extract categories (human-readable)
        categories_tags = off_product.get('categories_tags', [])
        primary_category = None
        if categories_tags:
            # Take the most specific (usually last) category
            primary_category = categories_tags[-1].replace('en:', '').replace('-', ' ').title()

        # Extract labels
        labels_tags = off_product.get('labels_tags', [])
        labels = [tag.replace('en:', '').replace('-', ' ').title() for tag in labels_tags]

        # NOVA group description
        nova_descriptions = {
            1: "Unprocessed or minimally processed",
            2: "Processed culinary ingredients",
            3: "Processed foods",
            4: "Ultra-processed foods"
        }
        nova_group = off_product.get('nova_group')
        nova_description = nova_descriptions.get(nova_group, "Unknown") if nova_group else None

        return {
            # Identification
            'upc': off_product.get('code'),
            'product_name': off_product.get('product_name', 'Unknown Product'),
            'brand': off_product.get('brands'),
            'quantity': off_product.get('quantity'),
            'serving_size': off_product.get('serving_size'),

            # Images
            'image_url': off_product.get('image_url'),
            'image_front_url': off_product.get('image_front_url'),
            'image_front_small_url': off_product.get('image_front_small_url'),

            # Categories
            'primary_category': primary_category,
            'all_categories': off_product.get('categories'),

            # Nutrition (per 100g)
            'nutrition': {
                'calories_100g': safe_get(nutriments, 'energy-kcal_100g'),
                'protein_100g': safe_get(nutriments, 'proteins_100g'),
                'fat_100g': safe_get(nutriments, 'fat_100g'),
                'carbohydrates_100g': safe_get(nutriments, 'carbohydrates_100g'),
                'sugars_100g': safe_get(nutriments, 'sugars_100g'),
                'salt_100g': safe_get(nutriments, 'salt_100g'),
                'fiber_100g': safe_get(nutriments, 'fiber_100g'),
            },

            # Processing
            'nova_group': nova_group,
            'nova_description': nova_description,

            # Labels & Certifications
            'labels': labels,
            'has_organic': any('organic' in label.lower() for label in labels),
            'has_fair_trade': any('fair-trade' in tag for tag in labels_tags),

            # Open Food Facts Scores (for reference)
            'ecoscore': {
                'grade': off_product.get('ecoscore_grade'),
                'score': off_product.get('ecoscore_score'),
            },
            'nutriscore_grade': off_product.get('nutriscore_grade'),

            # Data Quality
            'data_completeness': off_product.get('completeness'),

            # Location
            'manufacturing_places': off_product.get('manufacturing_places'),
            'origins': off_product.get('origins'),

            # Ingredients (summary)
            'ingredients_text': off_product.get('ingredients_text'),
            'has_palm_oil': bool(off_product.get('ingredients_from_palm_oil_tags')),
        }

    @classmethod
    async def get_product_basic_info(cls, barcode: str) -> Optional[Dict[str, Any]]:
        """
        Fetch and extract basic product information

        Args:
            barcode: Product UPC/barcode

        Returns:
            Basic product info or None if not found
        """
        off_product = await cls.fetch_product(barcode)
        if not off_product:
            return None

        return cls.extract_basic_info(off_product)
