FROM python:3.10-slim-bookworm

# Install system dependencies (required for some python packages like geopandas/flet)
# Using bookworm (stable) ensures package availability.
# Flet on linux server (headless) might need basic GL libraries.
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY paginas/ ./paginas/
COPY mapa/ ./mapa/
# Note: We do NOT copy .env, secrets should be secrets manager or env vars in Cloud Run

# Port is provided by Cloud Run as PORT env var
ENV PORT=8080

# Run the application
# We use the port environment variable passed by usage of main.py update
CMD ["python", "paginas/main.py"]
