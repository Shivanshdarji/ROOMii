FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
# portaudio19-dev/libasound2-dev for PyAudio
# libglib2.0-0/libsm6/libxext6/libxrender-dev for OpenCV
RUN apt-get update && apt-get install -y \
    gcc \
    portaudio19-dev \
    libasound2-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from root (context must be root)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn gevent

# Copy backend code
COPY backend/ ./backend/

WORKDIR /app/backend

# Expose port
EXPOSE 5000

# Run with Gunicorn
# Worker class gevent is required for Socket.IO
CMD ["gunicorn", "-k", "gevent", "-w", "1", "--bind", "0.0.0.0:5000", "main:app"]
