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

Endpoints:
- `GET /health`
- `GET /api/echo?message=hi`
- `GET /api/db/ping`
- `GET /api/products/<upc>` – returns brand, product name, primary category, quantity, UPC, and manufacturing location. Example:

```json
{
  "status": "success",
  "source": "database",
  "data": {
    "brand": "Sample Foods",
    "name": "Organic Wheat Crackers",
    "product_name": "Organic Wheat Crackers",
    "primary_category": "Crackers",
    "quantity": "560 g",
    "upc": "0064100238220",
    "manufacturing_places": "Mississauga, Ontario"
  }
}
```

## Database

- All runtime configuration now lives in `.env`. Update the sample values there (e.g., `DATABASE_URL`).
- `OFF_BASE_URL` configures which Open Food Facts instance we call (defaults to `https://world.openfoodfacts.org/api/v2/product`); override it in `.env` if you need a different environment.
- Run `flask init-db` whenever the schema changes to keep Postgres in sync before ingesting Open Food Facts data.
- Flask automatically loads `.env` because `python-dotenv` is installed; no manual `export` commands needed.
