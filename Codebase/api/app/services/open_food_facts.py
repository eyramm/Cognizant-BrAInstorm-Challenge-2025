"""
Open Food Facts API Service
Handles fetching and parsing product data from Open Food Facts API
"""

import aiohttp
import os
from typing import Optional, Dict, Any, List
from datetime import datetime


class OpenFoodFactsService:
    """Service for interacting with Open Food Facts API"""

    @staticmethod
    def get_base_url() -> str:
        """Get base URL from environment or use default"""
        return os.getenv('OFF_BASE_URL', 'https://world.openfoodfacts.org')

    @staticmethod
    def get_timeout() -> int:
        """Get API timeout from environment or use default"""
        return int(os.getenv('OFF_API_TIMEOUT', '10'))

    @staticmethod
    def get_prices_base_url() -> str:
        """Get Prices API base URL from environment or use default"""
        return os.getenv('OFF_PRICES_BASE_URL', 'https://prices.openfoodfacts.org')

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
        'additives_tags',        # Food additive E-numbers
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

        Tries multiple barcode variants to handle UPC-A/EAN-13 differences.
        For example, if barcode "39978328151" fails, tries "0039978328151" next.

        Args:
            barcode: Product UPC/barcode

        Returns:
            Product data dict or None if not found
        """
        from ..utils.barcode import normalize_barcode

        base_url = cls.get_base_url()
        params = {'fields': ','.join(cls.REQUIRED_FIELDS)}

        # Get all possible barcode variants to try
        barcode_variants = normalize_barcode(barcode)
        print(f"[OFF] Trying barcode variants: {barcode_variants}")

        try:
            timeout = cls.get_timeout()
            headers = {'User-Agent': 'EcoApp/1.0 (Sustainability Product Scanner)'}
            async with aiohttp.ClientSession(headers=headers) as session:
                # Try each barcode variant until we find a match
                for variant in barcode_variants:
                    url = f"{base_url}/api/v2/product/{variant}.json"

                    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                        if response.status != 200:
                            print(f"[OFF] Barcode {variant}: HTTP {response.status}")
                            continue  # Try next variant

                        data = await response.json()

                        # Check if product was found
                        status = data.get('status')
                        status_verbose = data.get('status_verbose')

                        if status != 1:
                            print(f"[OFF] Barcode {variant}: status={status}, status_verbose={status_verbose}")
                            continue  # Try next variant

                        product = data.get('product')
                        if product:
                            print(f"[OFF] Barcode {variant}: Found! Product name: {product.get('product_name', 'N/A')}")
                            return product
                        else:
                            print(f"[OFF] Barcode {variant}: status=1 but no product data")
                            continue  # Try next variant

                # If we get here, none of the variants worked
                print(f"[OFF] Product not found for any variant of barcode {barcode}")
                return None

        except aiohttp.ClientError as e:
            # Log error but don't crash
            print(f"[OFF] Error fetching product {barcode}: {e}")
            return None
        except Exception as e:
            print(f"[OFF] Unexpected error fetching product {barcode}: {e}")
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

    @classmethod
    async def search_products_by_category(cls, category: str, page_size: int = 10) -> List[Dict[str, Any]]:
        """
        Search for products in a specific category using Open Food Facts Search API

        Args:
            category: Category tag (e.g., 'canned-meats', 'cereals')
            page_size: Number of results to return (default 10, max 100)

        Returns:
            List of product data dictionaries
        """
        base_url = cls.get_base_url()
        search_url = f"{base_url}/cgi/search.pl"

        # Build search parameters
        params = {
            'action': 'process',
            'tagtype_0': 'categories',
            'tag_contains_0': 'contains',
            'tag_0': category,
            'sort_by': 'unique_scans_n',  # Sort by popularity
            'page_size': min(page_size, 100),
            'json': 1,
            'fields': ','.join(cls.REQUIRED_FIELDS)
        }

        try:
            # Search API is slower than product API, use longer timeout
            search_timeout = max(cls.get_timeout(), 30)  # At least 30 seconds
            async with aiohttp.ClientSession() as session:
                headers = {'User-Agent': 'EcoApp/1.0 (Product Recommendation System)'}
                async with session.get(search_url, params=params, headers=headers,
                                      timeout=aiohttp.ClientTimeout(total=search_timeout)) as response:
                    if response.status != 200:
                        print(f"Search API returned status {response.status}")
                        return []

                    data = await response.json()
                    products = data.get('products', [])

                    # Return products (they're already in OFF format)
                    return products

        except aiohttp.ClientError as e:
            print(f"Error searching products in category {category}: {e}")
            import traceback
            traceback.print_exc()
            return []
        except Exception as e:
            print(f"Unexpected error searching products: {e}")
            import traceback
            traceback.print_exc()
            return []

    @classmethod
    async def fetch_product_price(cls, barcode: str, currency: str = 'USD') -> Optional[Dict[str, Any]]:
        """
        Fetch product price from Open Food Facts Prices API

        Args:
            barcode: Product UPC/barcode
            currency: Currency code (default: USD)

        Returns:
            Dict with price info or None if not found
            {
                'price': 3.99,
                'currency': 'USD',
                'date': '2025-01-15',
                'location_name': 'Walmart'
            }
        """
        prices_base_url = cls.get_prices_base_url()
        url = f"{prices_base_url}/api/v1/prices"

        params = {
            'product_code': barcode,
            'currency': currency,
            'page': 1,
            'size': 1  # Get only the most recent price
        }

        try:
            timeout = cls.get_timeout()
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
                    if response.status != 200:
                        return None

                    data = await response.json()

                    # Check if any prices were found
                    items = data.get('items', [])
                    if not items:
                        return None

                    # Get the most recent price (first item)
                    price_data = items[0]

                    return {
                        'price': price_data.get('price'),
                        'currency': price_data.get('currency'),
                        'date': price_data.get('date'),
                        'location_name': price_data.get('location', {}).get('name') if isinstance(price_data.get('location'), dict) else None
                    }

        except aiohttp.ClientError as e:
            print(f"Error fetching price for product {barcode}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error fetching price for product {barcode}: {e}")
            return None
