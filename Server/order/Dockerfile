FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service file
COPY order.py .
COPY .env* ./

# Expose port
EXPOSE 5002

# Run the service
CMD ["python", "order.py"]