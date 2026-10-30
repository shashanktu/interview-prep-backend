# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system dependencies required for OpenCV, MediaPipe, faster-whisper, PyMuPDF, and psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libegl1 \
    libgles2 \
    libgl1 \
    libglib2.0-0 \
    libxcb1 \
    libgomp1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*



# Set working directory
WORKDIR /app

# Copy dependency definition first for caching layer
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Expose port (Azure Web App default or custom PORT)
EXPOSE 8000

# Run FastAPI with uvicorn listening on 0.0.0.0 and port $PORT
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
