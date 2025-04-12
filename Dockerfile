# Use Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
  PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install ffmpeg and other system dependencies
RUN apt-get update && \
  apt-get install -y ffmpeg mkvtoolnix fonts-dejavu-core && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Copy dependency files first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Set default entrypoint (can still override in docker run)
ENTRYPOINT ["python", "main.py"]
