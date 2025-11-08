# Flask API Starter

Simple Flask API scaffold with a health check and echo endpoint.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
export FLASK_APP=wsgi.py
flask run --reload
```

Endpoints:
- `GET /health`
- `GET /api/echo?message=hi`
