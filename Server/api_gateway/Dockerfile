# Server/api_gateway/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps required for some packages (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY api_gateway.py .
COPY gateway_config.yaml .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

EXPOSE 8000

# Run Gunicorn with 2 workers and 120s timeout (matches other services)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "api_gateway:app"]