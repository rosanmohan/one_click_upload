FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app ./app
COPY .env . 
# Note: In production, .env should not be copied. specific env vars should be injected by the host.
# However, for simplicity in this guide, we copy it, but usually you use secret managers.
# We will rely on the host injecting env vars to override these or user mapping the file.

# Expose port
EXPOSE 8000

# Command to run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
