FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY api_gateway.py .
COPY gateway_config.yaml .

# Expose the gateway port
EXPOSE 8000

# Run the application
CMD ["python3", "api_gateway.py"]