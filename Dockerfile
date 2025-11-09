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
  # Run schema\n\
  psql $DATABASE_URL -f app/schema.sql || echo "Schema already exists"\n\
  \n\
  # Run all migrations in order\n\
  if [ -d migrations ]; then\n\
    for migration in migrations/*.sql; do\n\
      if [ -f "$migration" ]; then\n\
        echo "Running migration: $migration"\n\
        psql $DATABASE_URL -f "$migration" || echo "Migration $migration failed or already applied"\n\
      fi\n\
    done\n\
  fi\n\
  \n\
  # Run seed data\n\
  if [ -d app/data ]; then\n\
    for seed_file in app/data/*.sql; do\n\
      if [ -f "$seed_file" ]; then\n\
        echo "Running seed: $seed_file"\n\
        psql $DATABASE_URL -f "$seed_file" || echo "Seed $seed_file failed or already applied"\n\
      fi\n\
    done\n\
  fi\n\
  \n\
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
