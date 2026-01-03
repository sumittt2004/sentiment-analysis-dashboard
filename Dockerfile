# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for caching)
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app/ ./app/
COPY config/ ./config/


# Create necessary directories
RUN mkdir -p data/cache data/logs models

# Expose port
EXPOSE 8050

# Set environment variable
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-u", "-m", "app.dashboard"]