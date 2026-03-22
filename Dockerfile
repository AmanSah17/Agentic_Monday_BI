# Unified Production Dockerfile
FROM python:3.10-slim

# Install system dependencies & Node.js (required for build.sh)
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the entire project
COPY . .

# Ensure build.sh is executable and run the standard build process
RUN chmod +x build.sh
RUN ./build.sh

# Render implicitly passes the PORT variable, we map FastAPI directly to it
CMD python -m uvicorn founder_bi_agent.backend.api:app --host 0.0.0.0 --port ${PORT:-8000}
