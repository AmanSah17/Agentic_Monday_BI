# Unified Production Dockerfile
FROM python:3.10-slim

# Install system dependencies & Node.js
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency files first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the code
COPY . .

# Run the build script to bundle frontend
RUN chmod +x build.sh
RUN ./build.sh

# Environment variables for production
ENV PORT=8000
EXPOSE 8000

# Start the unified server
CMD ["python", "-m", "uvicorn", "founder_bi_agent.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
