FROM python:3.10-slim

WORKDIR /app

# Install dependencies explicitly to prevent caching rebuilds
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bind the underlying monolithic package code
COPY . /app

# Render passes the PORT variable automatically, we use standard fallback bindings
CMD python -m uvicorn founder_bi_agent.backend.api:app --host 0.0.0.0 --port ${PORT:-8000}
