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

- `GET /health` - Health check
- `GET /api/echo?message=hi` - Echo test
- `GET /api/db/ping` - Database connection test
- `GET /api/products/<barcode>` - Get basic product info (includes images)
- `GET /api/products/<barcode>?sustainability_score=true` - Get product with sustainability metrics (4 metrics: Raw Materials, Packaging, Transportation, Climate Efficiency)
  - Optional params: `lat=<latitude>`, `lon=<longitude>` for transportation calculations

## Database

- All runtime configuration now lives in `.env`. Update the sample values there (e.g., `DATABASE_URL`).
- `OFF_BASE_URL` configures which Open Food Facts instance we call (defaults to `https://world.openfoodfacts.org/api/v2/product`); override it in `.env` if you need a different environment.
- Run `flask init-db` whenever the schema changes to keep Postgres in sync before ingesting Open Food Facts data.
- Seed the ingredient emission factors used by the Raw Materials score:
  ```bash
  psql -d ecoapp -f app/data/seed_emission_factors.sql
  ```
- Flask automatically loads `.env` because `python-dotenv` is installed; no manual `export` commands needed.
