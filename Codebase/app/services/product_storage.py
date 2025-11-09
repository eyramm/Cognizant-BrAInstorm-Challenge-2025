"""
Product Storage Service
Handles saving Open Food Facts product data into our database
"""

from typing import Dict, Any, Optional, List
import re
from datetime import datetime


class ProductStorageService:
    """Service for storing product data in the database"""

    @staticmethod
    def parse_quantity(quantity_str: Optional[str]) -> Optional[float]:
        """
        Parse quantity string to grams
        Examples: "560", "560g", "1.5 kg" -> grams as float
        """
        if not quantity_str:
            return None

        # Remove spaces and convert to lowercase
        qty = str(quantity_str).strip().lower()

        # Extract number
        match = re.search(r'(\d+\.?\d*)', qty)
        if not match:
            return None

        value = float(match.group(1))

        # Convert to grams based on unit
        if 'kg' in qty:
            return value * 1000
        elif 'lb' in qty or 'pound' in qty:
            return value * 453.592
        elif 'oz' in qty or 'ounce' in qty:
            return value * 28.3495
        else:
            # Assume grams if no unit or 'g'
            return value

    @staticmethod
    def parse_location(manufacturing_places: Optional[str]) -> Dict[str, Optional[str]]:
        """
        Parse manufacturing location string
        Example: "Mississauga, Ontario" -> city, region, country
        """
        if not manufacturing_places:
            return {'city': None, 'region': None, 'country': None}

        parts = [p.strip() for p in manufacturing_places.split(',')]

        if len(parts) >= 3:
            # Format: "City, Region, Country"
            return {
                'city': parts[0],
                'region': parts[1],
                'country': parts[2]
            }
        elif len(parts) == 2:
            # Format: "City, Region" - can't determine country
            return {
                'city': parts[0],
                'region': parts[1],
                'country': None
            }
        elif len(parts) == 1:
            # Format: "Country" only
            return {
                'city': None,
                'region': None,
                'country': parts[0]
            }

        return {'city': None, 'region': None, 'country': None}

    @classmethod
    def get_or_create_manufacturer(cls, cursor, brand_name: Optional[str]) -> Optional[int]:
        """Get or create manufacturer and return ID"""
        if not brand_name:
            return None

        # Check if exists
        cursor.execute(
            "SELECT id FROM manufacturers WHERE name = %s",
            (brand_name,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Create new
        cursor.execute(
            "INSERT INTO manufacturers (name) VALUES (%s) RETURNING id",
            (brand_name,)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_category(cls, cursor, tag: str, name: str, level: int = 1) -> int:
        """Get or create category and return ID"""
        # Check if exists
        cursor.execute(
            "SELECT id FROM categories WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Create slug from tag
        slug = tag.replace('en:', '').replace('-', '_')

        # Create new
        cursor.execute(
            """INSERT INTO categories (tag, name, slug, level)
               VALUES (%s, %s, %s, %s)
               RETURNING id""",
            (tag, name, slug, level)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_food_group(cls, cursor, tag: str) -> int:
        """Get or create food group and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()

        cursor.execute(
            "SELECT id FROM food_groups WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO food_groups (tag, name) VALUES (%s, %s) RETURNING id",
            (tag, name)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_ingredient(cls, cursor, tag: str, vegan: Optional[str] = None,
                                 vegetarian: Optional[str] = None,
                                 is_palm_oil: bool = False) -> int:
        """Get or create ingredient and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()

        cursor.execute(
            "SELECT id FROM ingredients WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute(
            """INSERT INTO ingredients (tag, name, vegan_status, vegetarian_status, is_from_palm_oil)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (tag, name, vegan, vegetarian, is_palm_oil)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_allergen(cls, cursor, tag: str) -> int:
        """Get or create allergen and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()

        cursor.execute(
            "SELECT id FROM allergens WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO allergens (tag, name) VALUES (%s, %s) RETURNING id",
            (tag, name)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_label(cls, cursor, tag: str) -> int:
        """Get or create label and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()
        slug = tag.replace('en:', '')

        cursor.execute(
            "SELECT id FROM labels WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Determine bonus points based on label type
        bonus_points = 0
        label_category = 'other'

        if 'organic' in tag:
            bonus_points = 15
            label_category = 'environmental'
        elif 'fair-trade' in tag or 'rainforest-alliance' in tag or 'msc' in tag:
            bonus_points = 10
            label_category = 'social'
        elif 'fsc' in tag:
            bonus_points = 5
            label_category = 'environmental'

        cursor.execute(
            """INSERT INTO labels (tag, name, slug, label_category, bonus_points)
               VALUES (%s, %s, %s, %s, %s)
               RETURNING id""",
            (tag, name, slug, label_category, bonus_points)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_packaging_material(cls, cursor, tag: str) -> int:
        """Get or create packaging material and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()
        slug = tag.replace('en:', '')

        cursor.execute(
            "SELECT id FROM packaging_materials WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        # Default scores (can be improved with actual data)
        # Tuple: (recyclability, recycling_rate, biodegradability, transport, env_score, adjustment, co2_per_kg)
        scores = {
            'cardboard': (95, 62, 100, 95, 87, 10, 0.7),
            'paper': (95, 62, 100, 95, 87, 10, 0.5),
            'plastic': (15, 9, 0, 95, 23, -15, 4.0),
            'pet': (85, 29, 5, 95, 28, -8, 3.5),
            'hdpe': (80, 28, 5, 95, 26, -10, 2.8),
            'glass': (100, 31, 0, 20, 51, 0, 0.9),
            'aluminum': (100, 50, 0, 90, 68, 5, 8.5),
            'aluminium': (100, 50, 0, 90, 68, 5, 8.5),
            'metal': (100, 50, 0, 90, 68, 5, 6.0),
            'steel': (100, 45, 0, 88, 65, 3, 2.0),
            'tin': (100, 45, 0, 88, 65, 3, 2.2),
        }

        # Get scores or use defaults
        material_key = slug.lower()
        co2_per_kg = None
        for key in scores:
            if key in material_key:
                recyclability, recycling_rate, biodegradability, transport, env_score, adjustment, co2_per_kg = scores[key]
                break
        else:
            # Default moderate scores
            recyclability, recycling_rate, biodegradability, transport, env_score, adjustment = (50, 25, 10, 75, 40, -5)
            co2_per_kg = 3.0  # Default moderate CO2 emissions

        cursor.execute(
            """INSERT INTO packaging_materials
               (tag, name, slug, recyclability_score, recycling_rate_pct,
                biodegradability_score, transport_impact_score,
                environmental_score, score_adjustment, production_kg_co2_per_kg)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
               RETURNING id""",
            (tag, name, slug, recyclability, recycling_rate,
             biodegradability, transport, env_score, adjustment, co2_per_kg)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_packaging_shape(cls, cursor, tag: str) -> int:
        """Get or create packaging shape and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()

        cursor.execute(
            "SELECT id FROM packaging_shapes WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO packaging_shapes (tag, name) VALUES (%s, %s) RETURNING id",
            (tag, name)
        )
        return cursor.fetchone()[0]

    @classmethod
    def get_or_create_recycling_instruction(cls, cursor, tag: str) -> int:
        """Get or create recycling instruction and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()

        cursor.execute(
            "SELECT id FROM recycling_instructions WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO recycling_instructions (tag, name) VALUES (%s, %s) RETURNING id",
            (tag, name)
        )
        return cursor.fetchone()[0]

    @classmethod
    def extract_country_code(cls, tag: str) -> Optional[str]:
        """
        Extract ISO country code from tag if possible
        Examples: en:united-states -> US, en:canada -> CA
        """
        # Remove 'en:' prefix
        country_name = tag.replace('en:', '').replace('-', ' ')

        # Try to extract 2-letter codes that are already in the tag
        # Some tags might be like "en:us" or "en:ca"
        clean_tag = tag.replace('en:', '')
        if len(clean_tag) == 2 and clean_tag.isalpha():
            return clean_tag.upper()

        # For now, return None - country codes can be added later via a lookup service
        # or by parsing the pycountry library
        return None

    @classmethod
    def get_or_create_country(cls, cursor, tag: str) -> int:
        """Get or create country and return ID"""
        name = tag.replace('en:', '').replace('-', ' ').title()
        code = cls.extract_country_code(tag)

        cursor.execute(
            "SELECT id FROM countries WHERE tag = %s",
            (tag,)
        )
        result = cursor.fetchone()
        if result:
            return result[0]

        cursor.execute(
            "INSERT INTO countries (tag, name, code) VALUES (%s, %s, %s) RETURNING id",
            (tag, name, code)
        )
        return cursor.fetchone()[0]

    @classmethod
    def save_product(cls, conn, off_product: Dict[str, Any]) -> int:
        """
        Save complete product data to database
        Returns product ID
        """
        with conn.cursor() as cursor:
            # Helper to safely get values
            def safe_get(data: dict, *keys, default=None):
                for key in keys:
                    if isinstance(data, dict):
                        data = data.get(key)
                    else:
                        return default
                    if data is None:
                        return default
                return data

            # 1. Get or create manufacturer
            brand_name = off_product.get('brands')
            manufacturer_id = cls.get_or_create_manufacturer(cursor, brand_name)

            # 2. Parse quantities
            quantity_grams = cls.parse_quantity(off_product.get('quantity'))
            serving_size_grams = cls.parse_quantity(off_product.get('serving_size'))

            # 3. Parse location
            location = cls.parse_location(off_product.get('manufacturing_places'))

            # 4. Check for palm oil
            has_palm_oil = bool(off_product.get('ingredients_from_palm_oil_tags'))

            # 5. Insert or update product
            upc = off_product.get('code')

            # Check if product exists
            cursor.execute("SELECT id FROM products WHERE upc = %s", (upc,))
            existing = cursor.fetchone()

            if existing:
                # Update existing product
                product_id = existing[0]
                cursor.execute(
                    """UPDATE products SET
                       product_name = %s,
                       brand_id = %s,
                       quantity = %s,
                       quantity_grams = %s,
                       serving_size = %s,
                       serving_size_grams = %s,
                       nova_group = %s,
                       food_groups_tags = %s,
                       manufacturing_places = %s,
                       manufacturing_city = %s,
                       manufacturing_region = %s,
                       manufacturing_country = %s,
                       ingredients_text = %s,
                       labels_text = %s,
                       packaging_text = %s,
                       has_palm_oil = %s,
                       ecoscore_grade = %s,
                       ecoscore_score = %s,
                       nutriscore_grade = %s,
                       completeness = %s,
                       image_url = %s,
                       image_small_url = %s,
                       raw_off_data = %s,
                       updated_at = NOW(),
                       last_updated_at = NOW()
                       WHERE id = %s""",
                    (
                        off_product.get('product_name'),
                        manufacturer_id,
                        off_product.get('quantity'),
                        quantity_grams,
                        off_product.get('serving_size'),
                        serving_size_grams,
                        off_product.get('nova_group'),
                        off_product.get('food_groups_tags', []),
                        off_product.get('manufacturing_places'),
                        location['city'],
                        location['region'],
                        location['country'],
                        off_product.get('ingredients_text'),
                        off_product.get('labels'),
                        off_product.get('packaging'),
                        has_palm_oil,
                        off_product.get('ecoscore_grade'),
                        off_product.get('ecoscore_score'),
                        off_product.get('nutriscore_grade'),
                        off_product.get('completeness'),
                        off_product.get('image_front_url'),
                        off_product.get('image_front_small_url'),
                        json.dumps(off_product),  # Store complete OFF data
                        product_id
                    )
                )
            else:
                # Insert new product
                cursor.execute(
                    """INSERT INTO products
                       (upc, product_name, brand_id, quantity, quantity_grams,
                        serving_size, serving_size_grams, nova_group, food_groups_tags,
                        manufacturing_places, manufacturing_city, manufacturing_region,
                        manufacturing_country, ingredients_text, labels_text, packaging_text,
                        has_palm_oil, ecoscore_grade, ecoscore_score, nutriscore_grade,
                        completeness, image_url, image_small_url, raw_off_data)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                       RETURNING id""",
                    (
                        upc,
                        off_product.get('product_name'),
                        manufacturer_id,
                        off_product.get('quantity'),
                        quantity_grams,
                        off_product.get('serving_size'),
                        serving_size_grams,
                        off_product.get('nova_group'),
                        off_product.get('food_groups_tags', []),
                        off_product.get('manufacturing_places'),
                        location['city'],
                        location['region'],
                        location['country'],
                        off_product.get('ingredients_text'),
                        off_product.get('labels'),
                        off_product.get('packaging'),
                        has_palm_oil,
                        off_product.get('ecoscore_grade'),
                        off_product.get('ecoscore_score'),
                        off_product.get('nutriscore_grade'),
                        off_product.get('completeness'),
                        off_product.get('image_front_url'),
                        off_product.get('image_front_small_url'),
                        json.dumps(off_product)  # Store complete OFF data
                    )
                )
                product_id = cursor.fetchone()[0]

            # 6. Save categories using UPSERT to prevent duplicates
            categories_tags = off_product.get('categories_tags', [])

            # First, clear is_primary for all existing categories for this product
            cursor.execute(
                "UPDATE product_categories SET is_primary = FALSE WHERE product_id = %s",
                (product_id,)
            )

            for idx, tag in enumerate(categories_tags):
                if tag.startswith('en:'):
                    name = tag.replace('en:', '').replace('-', ' ').title()
                    category_id = cls.get_or_create_category(cursor, tag, name, level=idx+1)
                    is_primary = (idx == len(categories_tags) - 1)  # Last one is primary

                    # Use ON CONFLICT to prevent duplicates
                    cursor.execute(
                        """INSERT INTO product_categories (product_id, category_id, is_primary, position)
                           VALUES (%s, %s, %s, %s)
                           ON CONFLICT (product_id, category_id)
                           DO UPDATE SET is_primary = EXCLUDED.is_primary, position = EXCLUDED.position""",
                        (product_id, category_id, is_primary, idx)
                    )

            # Remove categories that are no longer associated with this product
            if categories_tags:
                category_ids = [cls.get_or_create_category(cursor, tag, tag.replace('en:', '').replace('-', ' ').title(), level=idx+1)
                               for idx, tag in enumerate(categories_tags) if tag.startswith('en:')]
                if category_ids:
                    # Use ANY instead of IN with tuple
                    cursor.execute(
                        "DELETE FROM product_categories WHERE product_id = %s AND category_id != ALL(%s)",
                        (product_id, category_ids)
                    )

            # 7. Save food groups using UPSERT to prevent duplicates
            food_groups_tags = off_product.get('food_groups_tags', [])
            for idx, tag in enumerate(food_groups_tags):
                food_group_id = cls.get_or_create_food_group(cursor, tag)
                cursor.execute(
                    """INSERT INTO product_food_groups (product_id, food_group_id, position)
                       VALUES (%s, %s, %s)
                       ON CONFLICT (product_id, food_group_id)
                       DO UPDATE SET position = EXCLUDED.position""",
                    (product_id, food_group_id, idx)
                )

            # Remove food groups no longer associated
            if food_groups_tags:
                food_group_ids = [cls.get_or_create_food_group(cursor, tag) for tag in food_groups_tags]
                if food_group_ids:
                    cursor.execute(
                        "DELETE FROM product_food_groups WHERE product_id = %s AND food_group_id != ALL(%s)",
                        (product_id, food_group_ids)
                    )

            # 8. Save ingredients using UPSERT to prevent duplicates
            ingredients = off_product.get('ingredients', [])
            palm_oil_tags = off_product.get('ingredients_from_palm_oil_tags', [])

            ingredient_ids_list = []
            for idx, ingredient in enumerate(ingredients):
                tag = ingredient.get('id', '')
                if tag:
                    vegan = ingredient.get('vegan')
                    vegetarian = ingredient.get('vegetarian')
                    is_palm = tag in palm_oil_tags

                    ingredient_id = cls.get_or_create_ingredient(
                        cursor, tag, vegan, vegetarian, is_palm
                    )
                    ingredient_ids_list.append(ingredient_id)

                    cursor.execute(
                        """INSERT INTO product_ingredients
                           (product_id, ingredient_id, percent_estimate, percent_min, percent_max,
                            rank, raw_text, contains_palm_oil, is_vegan, is_vegetarian)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                           ON CONFLICT (product_id, ingredient_id)
                           DO UPDATE SET
                               percent_estimate = EXCLUDED.percent_estimate,
                               percent_min = EXCLUDED.percent_min,
                               percent_max = EXCLUDED.percent_max,
                               rank = EXCLUDED.rank,
                               raw_text = EXCLUDED.raw_text,
                               contains_palm_oil = EXCLUDED.contains_palm_oil,
                               is_vegan = EXCLUDED.is_vegan,
                               is_vegetarian = EXCLUDED.is_vegetarian""",
                        (
                            product_id,
                            ingredient_id,
                            ingredient.get('percent_estimate'),
                            ingredient.get('percent_min'),
                            ingredient.get('percent_max'),
                            idx + 1,
                            ingredient.get('text'),
                            is_palm,
                            vegan == 'yes',
                            vegetarian == 'yes'
                        )
                    )

            # Remove ingredients no longer in the product
            if ingredient_ids_list:
                cursor.execute(
                    "DELETE FROM product_ingredients WHERE product_id = %s AND ingredient_id != ALL(%s)",
                    (product_id, ingredient_ids_list)
                )

            # 9. Save allergens using UPSERT to prevent duplicates
            allergens_tags = off_product.get('allergens_tags', [])
            allergen_ids_list = []
            for tag in allergens_tags:
                allergen_id = cls.get_or_create_allergen(cursor, tag)
                allergen_ids_list.append(allergen_id)
                cursor.execute(
                    """INSERT INTO product_allergens (product_id, allergen_id)
                       VALUES (%s, %s)
                       ON CONFLICT (product_id, allergen_id) DO NOTHING""",
                    (product_id, allergen_id)
                )

            # Remove allergens no longer associated
            if allergen_ids_list:
                cursor.execute(
                    "DELETE FROM product_allergens WHERE product_id = %s AND allergen_id != ALL(%s)",
                    (product_id, allergen_ids_list)
                )

            # 10. Save labels using UPSERT to prevent duplicates
            labels_tags = off_product.get('labels_tags', [])
            label_ids_list = []
            for tag in labels_tags:
                label_id = cls.get_or_create_label(cursor, tag)
                label_ids_list.append(label_id)
                cursor.execute(
                    """INSERT INTO product_labels (product_id, label_id)
                       VALUES (%s, %s)
                       ON CONFLICT (product_id, label_id) DO NOTHING""",
                    (product_id, label_id)
                )

            # Remove labels no longer associated
            if label_ids_list:
                cursor.execute(
                    "DELETE FROM product_labels WHERE product_id = %s AND label_id != ALL(%s)",
                    (product_id, label_ids_list)
                )

            # 11. Save packaging - delete and re-insert (no natural key for ON CONFLICT)
            cursor.execute("DELETE FROM packagings WHERE product_id = %s", (product_id,))

            packagings = off_product.get('packagings', [])
            for packaging in packagings:
                material_tag = packaging.get('material', '')
                shape_tag = packaging.get('shape', '')
                recycling_tag = packaging.get('recycling', '')

                material_id = cls.get_or_create_packaging_material(cursor, material_tag) if material_tag else None
                shape_id = cls.get_or_create_packaging_shape(cursor, shape_tag) if shape_tag else None
                recycling_id = cls.get_or_create_recycling_instruction(cursor, recycling_tag) if recycling_tag else None

                cursor.execute(
                    """INSERT INTO packagings
                       (product_id, material_id, shape_id, recycling_id, number_of_units,
                        material_text, shape_text, recycling_text)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (
                        product_id,
                        material_id,
                        shape_id,
                        recycling_id,
                        packaging.get('number_of_units', 1),
                        material_tag,
                        shape_tag,
                        recycling_tag
                    )
                )

            # 12. Save nutriments using UPSERT (primary key is product_id)
            nutriments = off_product.get('nutriments', {})
            cursor.execute(
                """INSERT INTO nutriments
                   (product_id, calories_100g, energy_kj_100g, protein_100g, fat_100g,
                    carbs_100g, sugars_100g, fiber_100g, salt_100g, saturated_fat_100g, sodium_100g)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   ON CONFLICT (product_id)
                   DO UPDATE SET
                       calories_100g = EXCLUDED.calories_100g,
                       energy_kj_100g = EXCLUDED.energy_kj_100g,
                       protein_100g = EXCLUDED.protein_100g,
                       fat_100g = EXCLUDED.fat_100g,
                       carbs_100g = EXCLUDED.carbs_100g,
                       sugars_100g = EXCLUDED.sugars_100g,
                       fiber_100g = EXCLUDED.fiber_100g,
                       salt_100g = EXCLUDED.salt_100g,
                       saturated_fat_100g = EXCLUDED.saturated_fat_100g,
                       sodium_100g = EXCLUDED.sodium_100g""",
                (
                    product_id,
                    nutriments.get('energy-kcal_100g'),
                    nutriments.get('energy_100g'),
                    nutriments.get('proteins_100g'),
                    nutriments.get('fat_100g'),
                    nutriments.get('carbohydrates_100g'),
                    nutriments.get('sugars_100g'),
                    nutriments.get('fiber_100g'),
                    nutriments.get('salt_100g'),
                    nutriments.get('saturated-fat_100g'),
                    nutriments.get('sodium_100g')
                )
            )

            # 13. Save countries using UPSERT
            countries_tags = off_product.get('countries_tags', [])
            country_ids_list = []
            for idx, tag in enumerate(countries_tags):
                country_id = cls.get_or_create_country(cursor, tag)
                country_ids_list.append(country_id)
                cursor.execute(
                    """INSERT INTO product_countries (product_id, country_id, relation, position)
                       VALUES (%s, %s, %s, %s)
                       ON CONFLICT (product_id, country_id, relation)
                       DO UPDATE SET position = EXCLUDED.position""",
                    (product_id, country_id, 'sold_in', idx)
                )

            # Remove countries no longer associated
            if country_ids_list:
                cursor.execute(
                    "DELETE FROM product_countries WHERE product_id = %s AND country_id != ALL(%s) AND relation = 'sold_in'",
                    (product_id, country_ids_list)
                )

            conn.commit()
            return product_id
