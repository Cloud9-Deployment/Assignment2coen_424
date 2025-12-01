FROM python:3.11-slim

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY event.py .

# Expose the event service port
EXPOSE 5003

# Run the application
CMD ["python3", "event.py"]