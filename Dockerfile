# Multi-stage Docker build for taxi streaming system
FROM python:3.9-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    ffmpeg \
    libopencv-dev \
    python3-opencv \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application code
COPY . .

# Create update script
RUN echo '#!/bin/bash\n\
echo "🔄 Checking for updates..."\n\
cd /app\n\
git fetch origin\n\
LOCAL=$(git rev-parse HEAD)\n\
REMOTE=$(git rev-parse origin/main)\n\
if [ "$LOCAL" != "$REMOTE" ]; then\n\
    echo "📥 Updates found, pulling changes..."\n\
    git pull origin main\n\
    pip install -r requirements.txt\n\
    echo "✅ Update complete, restarting..."\n\
    pkill -f "python.*api_server.py" || true\n\
    python3 api_server.py &\n\
else\n\
    echo "✅ Already up to date"\n\
fi' > /app/update.sh && chmod +x /app/update.sh

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command - run both main.py and api_server.py
CMD ["sh", "-c", "python3 main.py --config config/HDJ864L_live.yaml & python3 api_server.py & wait"]
