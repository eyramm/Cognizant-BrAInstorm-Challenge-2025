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

## Database

- All runtime configuration now lives in `.env`. Update the sample values there (e.g., `DATABASE_URL`).
- Run `flask init-db` whenever the schema changes to keep Postgres in sync before ingesting Open Food Facts data.
- Flask automatically loads `.env` because `python-dotenv` is installed; no manual `export` commands needed.
