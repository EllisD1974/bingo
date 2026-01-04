# Base image
FROM python:3.13.9-slim

# Set working directory
WORKDIR /app

# Install system deps for cloudflared (optional if you only want API)
RUN apt-get update && apt-get install -y wget ca-certificates && apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY ../requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY .. .

# Expose FastAPI port
EXPOSE 8000

# Start uvicorn when container runs
CMD ["uvicorn", "api_main:app", "--host", "0.0.0.0", "--port", "8000"]
