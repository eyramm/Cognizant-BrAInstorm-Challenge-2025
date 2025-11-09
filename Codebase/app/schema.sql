BEGIN;

--
-- Reference and Lookup Tables
--

-- Manufacturers/Brands
CREATE TABLE IF NOT EXISTS manufacturers (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    normalized_name TEXT GENERATED ALWAYS AS (lower(name)) STORED,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Categories with hierarchical structure
CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    tag TEXT UNIQUE NOT NULL,                -- OFF tag: en:waffles
    display_name VARCHAR(100),
    description TEXT,
    level SMALLINT NOT NULL,
    parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_categories_parent ON categories(parent_id);
CREATE INDEX IF NOT EXISTS idx_categories_level ON categories(level);
CREATE INDEX IF NOT EXISTS idx_categories_slug ON categories(slug);
CREATE INDEX IF NOT EXISTS idx_categories_tag ON categories(tag);

-- Food Groups
CREATE TABLE IF NOT EXISTS food_groups (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ingredients
CREATE TABLE IF NOT EXISTS ingredients (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name TEXT,
    vegan_status TEXT,
    vegetarian_status TEXT,
    is_from_palm_oil BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Ingredient Emission Factors (for sustainability scoring)
CREATE TABLE IF NOT EXISTS ingredient_emission_factors (
    id SERIAL PRIMARY KEY,
    ingredient_name VARCHAR(255) NOT NULL,
    ingredient_tag VARCHAR(255) UNIQUE NOT NULL,
    category VARCHAR(100),
    kg_co2_per_kg DECIMAL(10,4) NOT NULL,
    data_source VARCHAR(100),
    confidence VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_ingredient_emission_tag ON ingredient_emission_factors(ingredient_tag);
CREATE INDEX IF NOT EXISTS idx_ingredient_emission_category ON ingredient_emission_factors(category);

-- Allergens
CREATE TABLE IF NOT EXISTS allergens (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Labels/Certifications with scoring metadata
CREATE TABLE IF NOT EXISTS labels (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    label_category VARCHAR(50),              -- environmental, social, health, quality
    display_name VARCHAR(100),
    description TEXT,
    icon VARCHAR(10),                        -- Emoji or icon identifier
    color VARCHAR(20),                       -- UI badge color
    bonus_points INTEGER DEFAULT 0,          -- Sustainability bonus points
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_labels_category ON labels(label_category);
CREATE INDEX IF NOT EXISTS idx_labels_tag ON labels(tag);

-- Packaging Materials with environmental scoring
CREATE TABLE IF NOT EXISTS packaging_materials (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    slug VARCHAR(100) UNIQUE NOT NULL,
    material_subtype VARCHAR(100),

    -- Environmental Scoring (0-100)
    recyclability_score INTEGER NOT NULL,
    recycling_rate_pct DECIMAL(5,2),
    biodegradability_score INTEGER NOT NULL,
    transport_impact_score INTEGER NOT NULL,
    environmental_score INTEGER NOT NULL,
    score_adjustment INTEGER NOT NULL,       -- -15 to +10

    -- GHG emissions
    production_kg_co2_per_kg DECIMAL(10,4),

    -- Additional info
    recycling_code VARCHAR(10),
    biodegradation_time VARCHAR(100),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_packaging_materials_tag ON packaging_materials(tag);
CREATE INDEX IF NOT EXISTS idx_packaging_materials_slug ON packaging_materials(slug);

-- Packaging Shapes
CREATE TABLE IF NOT EXISTS packaging_shapes (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Recycling Instructions
CREATE TABLE IF NOT EXISTS recycling_instructions (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    name TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Countries
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,                -- en:canada
    name TEXT NOT NULL,
    code VARCHAR(2),                         -- ISO 2-letter code
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Grid Carbon Intensity (deprecated - energy source metric removed)
-- CREATE TABLE IF NOT EXISTS grid_carbon_intensity (
--     id SERIAL PRIMARY KEY,
--     country_code VARCHAR(2) NOT NULL,
--     region VARCHAR(100),
--     grid_name VARCHAR(100),
--     g_co2_per_kwh DECIMAL(10,2) NOT NULL,
--     year INTEGER,
--     data_source VARCHAR(100),
--     created_at TIMESTAMPTZ DEFAULT NOW()
-- );
--
-- CREATE INDEX IF NOT EXISTS idx_grid_intensity_country ON grid_carbon_intensity(country_code);
-- CREATE INDEX IF NOT EXISTS idx_grid_intensity_region ON grid_carbon_intensity(region);

-- Agribalyse Categories (baseline scoring)
CREATE TABLE IF NOT EXISTS agribalyse_categories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES categories(id),
    agribalyse_code VARCHAR(20),
    base_score INTEGER NOT NULL CHECK (base_score BETWEEN 0 AND 70),
    typical_co2_kg_per_kg DECIMAL(10,4),
    energy_intensity_kwh_per_kg DECIMAL(10,4),
    data_source VARCHAR(100) DEFAULT 'Agribalyse 3.1',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agribalyse_category ON agribalyse_categories(category_id);
CREATE INDEX IF NOT EXISTS idx_agribalyse_code ON agribalyse_categories(agribalyse_code);

--
-- Core Product Tables
--

CREATE TABLE IF NOT EXISTS products (
    id BIGSERIAL PRIMARY KEY,

    -- Product Identification
    upc TEXT UNIQUE NOT NULL,
    product_name TEXT NOT NULL,
    brand_id INTEGER REFERENCES manufacturers(id),

    -- Quantity
    quantity TEXT,                           -- Raw from OFF
    quantity_grams DECIMAL(10,2),            -- Parsed numeric
    serving_size TEXT,                       -- Raw from OFF
    serving_size_grams DECIMAL(10,2),        -- Parsed numeric

    -- Processing & Classification
    nova_group SMALLINT CHECK (nova_group BETWEEN 1 AND 4),
    food_groups_tags TEXT[],                 -- For Agribalyse matching

    -- Manufacturing & Origin
    manufacturing_places TEXT,               -- Raw from OFF
    manufacturing_city VARCHAR(100),         -- Parsed
    manufacturing_region VARCHAR(100),       -- Parsed
    manufacturing_country VARCHAR(100),      -- Parsed

    -- Ingredients (text versions)
    ingredients_text TEXT,
    labels_text TEXT,
    packaging_text TEXT,
    has_palm_oil BOOLEAN DEFAULT FALSE,

    -- Open Food Facts Reference Scores
    ecoscore_grade CHAR(1),
    ecoscore_score SMALLINT,
    nutriscore_grade CHAR(1),

    -- Data Quality
    completeness NUMERIC(5,2),

    -- Images
    image_url TEXT,                          -- Full-size product image
    image_small_url TEXT,                    -- Thumbnail image (200px)

    -- Raw Data Storage
    raw_off_data JSONB,                      -- Full OFF product object

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    first_scanned_at TIMESTAMPTZ DEFAULT NOW(),
    last_updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_products_upc ON products(upc);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_nova_group ON products(nova_group);
CREATE INDEX IF NOT EXISTS idx_products_manufacturing_country ON products(manufacturing_country);

--
-- Junction Tables (Many-to-Many Relationships)
--

CREATE TABLE IF NOT EXISTS product_categories (
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
    is_primary BOOLEAN DEFAULT FALSE,
    position SMALLINT,
    PRIMARY KEY (product_id, category_id)
);

CREATE INDEX IF NOT EXISTS idx_product_categories_product ON product_categories(product_id);
CREATE INDEX IF NOT EXISTS idx_product_categories_category ON product_categories(category_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_one_primary_category
    ON product_categories(product_id)
    WHERE is_primary = TRUE;

CREATE TABLE IF NOT EXISTS product_food_groups (
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    food_group_id INTEGER REFERENCES food_groups(id) ON DELETE CASCADE,
    position SMALLINT,
    PRIMARY KEY (product_id, food_group_id)
);

CREATE INDEX IF NOT EXISTS idx_product_food_groups_product ON product_food_groups(product_id);
CREATE INDEX IF NOT EXISTS idx_product_food_groups_group ON product_food_groups(food_group_id);

CREATE TABLE IF NOT EXISTS product_ingredients (
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    ingredient_id INTEGER REFERENCES ingredients(id) ON DELETE CASCADE,
    percent_estimate NUMERIC(6,3),
    percent_min NUMERIC(6,3),
    percent_max NUMERIC(6,3),
    rank SMALLINT,
    raw_text TEXT,
    contains_palm_oil BOOLEAN DEFAULT FALSE,
    is_vegan BOOLEAN,
    is_vegetarian BOOLEAN,
    is_allergen BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (product_id, ingredient_id)
);

CREATE INDEX IF NOT EXISTS idx_product_ingredients_product ON product_ingredients(product_id);
CREATE INDEX IF NOT EXISTS idx_product_ingredients_ingredient ON product_ingredients(ingredient_id);
CREATE INDEX IF NOT EXISTS idx_product_ingredients_rank ON product_ingredients(product_id, rank);

CREATE TABLE IF NOT EXISTS product_allergens (
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    allergen_id INTEGER REFERENCES allergens(id) ON DELETE CASCADE,
    PRIMARY KEY (product_id, allergen_id)
);

CREATE INDEX IF NOT EXISTS idx_product_allergens_product ON product_allergens(product_id);
CREATE INDEX IF NOT EXISTS idx_product_allergens_allergen ON product_allergens(allergen_id);

CREATE TABLE IF NOT EXISTS product_labels (
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    label_id INTEGER REFERENCES labels(id) ON DELETE CASCADE,
    verified BOOLEAN DEFAULT FALSE,
    verification_source VARCHAR(100),
    PRIMARY KEY (product_id, label_id)
);

CREATE INDEX IF NOT EXISTS idx_product_labels_product ON product_labels(product_id);
CREATE INDEX IF NOT EXISTS idx_product_labels_label ON product_labels(label_id);

-- Packagings (products can have multiple packaging components)
CREATE TABLE IF NOT EXISTS packagings (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    material_id INTEGER REFERENCES packaging_materials(id),
    shape_id INTEGER REFERENCES packaging_shapes(id),
    recycling_id INTEGER REFERENCES recycling_instructions(id),
    number_of_units INTEGER,
    weight_percentage DECIMAL(5,2),          -- Percentage of total packaging
    material_text TEXT,
    shape_text TEXT,
    recycling_text TEXT
);

CREATE INDEX IF NOT EXISTS idx_packagings_product ON packagings(product_id);
CREATE INDEX IF NOT EXISTS idx_packagings_material ON packagings(material_id);
CREATE INDEX IF NOT EXISTS idx_packagings_shape ON packagings(shape_id);

-- Nutriments (1:1 with products)
CREATE TABLE IF NOT EXISTS nutriments (
    product_id BIGINT PRIMARY KEY REFERENCES products(id) ON DELETE CASCADE,
    calories_100g NUMERIC(7,2),
    energy_kj_100g NUMERIC(9,2),
    protein_100g NUMERIC(7,3),
    fat_100g NUMERIC(7,3),
    carbs_100g NUMERIC(7,3),
    sugars_100g NUMERIC(7,3),
    fiber_100g NUMERIC(7,3),
    salt_100g NUMERIC(7,4),
    saturated_fat_100g NUMERIC(7,3),
    sodium_100g NUMERIC(7,4)
);

-- Product Countries with fixed enum
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'country_relation') THEN
        CREATE TYPE country_relation AS ENUM ('sold_in', 'manufacturing', 'ingredients_from');
    END IF;
END$$;

CREATE TABLE IF NOT EXISTS product_countries (
    product_id BIGINT REFERENCES products(id) ON DELETE CASCADE,
    country_id INTEGER REFERENCES countries(id) ON DELETE CASCADE,
    relation country_relation NOT NULL,
    position SMALLINT,
    PRIMARY KEY (product_id, country_id, relation)
);

CREATE INDEX IF NOT EXISTS idx_product_countries_product ON product_countries(product_id);
CREATE INDEX IF NOT EXISTS idx_product_countries_country ON product_countries(country_id);
CREATE INDEX IF NOT EXISTS idx_product_countries_relation ON product_countries(relation);

--
-- Sustainability Scoring Tables
--

CREATE TABLE IF NOT EXISTS sustainability_scores (
    id BIGSERIAL PRIMARY KEY,
    product_id BIGINT UNIQUE REFERENCES products(id) ON DELETE CASCADE,

    -- Component Scores (point adjustments)
    raw_materials_score INTEGER,
    transportation_score INTEGER,
    packaging_score INTEGER,

    -- Metric Scores
    climate_efficiency_score INTEGER,       -- CO2 per 100 calories

    -- Adjustments
    label_bonus INTEGER DEFAULT 0,
    nova_penalty INTEGER DEFAULT 0,
    palm_oil_penalty INTEGER DEFAULT 0,

    -- Total
    total_score INTEGER,                    -- 0-100
    grade CHAR(1),                          -- A-E

    -- Metadata
    confidence VARCHAR(20),                 -- High, Moderate, Low, Very Low
    confidence_score INTEGER,
    calculation_version VARCHAR(10),

    -- Timestamps
    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sustainability_scores_product ON sustainability_scores(product_id);
CREATE INDEX IF NOT EXISTS idx_sustainability_scores_total ON sustainability_scores(total_score);
CREATE INDEX IF NOT EXISTS idx_sustainability_scores_grade ON sustainability_scores(grade);

-- Score Breakdown (detailed metrics)
CREATE TABLE IF NOT EXISTS score_breakdown (
    id BIGSERIAL PRIMARY KEY,
    score_id BIGINT REFERENCES sustainability_scores(id) ON DELETE CASCADE,

    -- GHG Emissions
    total_ghg_kg_co2 DECIMAL(10,4),
    raw_materials_ghg DECIMAL(10,4),
    manufacturing_ghg DECIMAL(10,4),
    transportation_ghg DECIMAL(10,4),
    packaging_ghg DECIMAL(10,4),

    -- Climate Efficiency
    co2_per_100_calories DECIMAL(10,4),

    -- Energy
    total_energy_kwh DECIMAL(10,4),
    grid_intensity_g_co2_kwh DECIMAL(10,2),

    -- Transportation
    transport_distance_km INTEGER,
    transport_mode VARCHAR(50),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_score_breakdown_score ON score_breakdown(score_id);

--
-- Helper Functions
--

-- Get full category path
CREATE OR REPLACE FUNCTION get_category_path(category_id INTEGER)
RETURNS TEXT AS $$
DECLARE
    path TEXT;
BEGIN
    WITH RECURSIVE category_tree AS (
        SELECT id, name, parent_id, 1 as depth
        FROM categories
        WHERE id = category_id

        UNION ALL

        SELECT c.id, c.name, c.parent_id, ct.depth + 1
        FROM categories c
        JOIN category_tree ct ON c.id = ct.parent_id
    )
    SELECT string_agg(name, ' > ' ORDER BY depth DESC)
    INTO path
    FROM category_tree;

    RETURN path;
END;
$$ LANGUAGE plpgsql;

-- Update timestamp trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply update trigger to products
DROP TRIGGER IF EXISTS update_products_updated_at ON products;
CREATE TRIGGER update_products_updated_at
    BEFORE UPDATE ON products
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Apply update trigger to sustainability_scores
DROP TRIGGER IF EXISTS update_scores_updated_at ON sustainability_scores;
CREATE TRIGGER update_scores_updated_at
    BEFORE UPDATE ON sustainability_scores
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

COMMIT;
