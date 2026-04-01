# Use an official Python runtime as a parent image
FROM python:3.11.6-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    firefox-esr \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory to /app
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs && \
    chmod -R 777 /app/logs

# Expose port
EXPOSE 8080

# Run main.py when the container launches
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080"]