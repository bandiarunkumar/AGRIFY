FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL and building packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm-rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir gunicorn psycopg2-binary

# Copy application source code
COPY . .

EXPOSE 5000

# Run via Gunicorn with extended timeout for LLM inference & Telemetry
CMD ["gunicorn", "--config", "gunicorn.conf.py", "api:app"]
