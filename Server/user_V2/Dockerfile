FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service file
COPY user_V2.py .
COPY .env* ./

# Expose port
EXPOSE 5001

# Run the service
CMD ["python", "user_V2.py"]