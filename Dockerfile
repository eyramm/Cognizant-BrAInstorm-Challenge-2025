# Use Python 3.12 official image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies including PostgreSQL client for migrations
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY Codebase/ /app/

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

# Create a startup script that runs migrations then starts the app
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Running database migrations..."\n\
if [ -n "$DATABASE_URL" ]; then\n\
  psql $DATABASE_URL -f app/schema.sql || echo "Schema already exists"\n\
  psql $DATABASE_URL -f app/data/seed_emission_factors.sql || echo "Emission factors already seeded"\n\
  psql $DATABASE_URL -f app/data/seed_packaging_materials.sql || echo "Packaging materials already seeded"\n\
  echo "Migrations completed"\n\
else\n\
  echo "WARNING: DATABASE_URL not set, skipping migrations"\n\
fi\n\
\n\
echo "Starting application..."\n\
exec gunicorn --bind 0.0.0.0:8080 --workers 4 --timeout 120 wsgi:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the startup script
CMD ["/app/start.sh"]
