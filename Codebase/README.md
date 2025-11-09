# Flask API Starter

Simple Flask API scaffold with a health check and echo endpoint.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

1. Copy the sample env file and update values as needed:
   ```bash
   cp .env.example .env
   ```
2. Create/update the database schema (uses `app/schema.sql`):
   ```bash
   flask init-db
   ```
3. Start the API:
   ```bash
   flask run --reload
   ```

## API Endpoints

**Health & Testing**
- `GET /health`
- `GET /api/echo?message=<text>`
- `GET /api/db/ping`

**Products**
- `GET /api/products/<barcode>`
- `GET /api/products/<barcode>?ingredients=true`
- `GET /api/products/<barcode>?sustainability_score=true`
- `GET /api/products/<barcode>?recommendations=true`
- `GET /api/products/<barcode>?sustainability_score=true&ingredients=true&recommendations=true`

**Query Parameters:**
- `sustainability_score` - `true` to include sustainability metrics
- `ingredients` - `true` to include ingredient health analysis (good/caution/harmful)
- `recommendations` - `true` to include better alternative product suggestions
- `lat` - Latitude for transportation calculations
- `lon` - Longitude for transportation calculations

## Database

- All runtime configuration now lives in `.env`. Update the sample values there (e.g., `DATABASE_URL`).
- `OFF_BASE_URL` configures which Open Food Facts instance we call (defaults to `https://world.openfoodfacts.org`); override it in `.env` if you need a different environment.
- Run `flask init-db` whenever the schema changes to keep Postgres in sync before ingesting Open Food Facts data.
- Run migrations:
  ```bash
  psql -d ecoapp -f migrations/001_add_image_columns.sql
  psql -d ecoapp -f migrations/002_add_ingredient_health_classification.sql
  psql -d ecoapp -f migrations/003_add_cached_transportation.sql
  ```
- Seed the ingredient emission factors and health classifications:
  ```bash
  psql -d ecoapp -f app/data/seed_emission_factors.sql
  psql -d ecoapp -f app/data/seed_harmful_ingredients.sql
  ```
- Set default transportation scores for existing products:
  ```bash
  psql -d ecoapp -c "UPDATE products SET transportation_score = 0 WHERE transportation_score IS NULL;"
  ```
- Flask automatically loads `.env` because `python-dotenv` is installed; no manual `export` commands needed.
