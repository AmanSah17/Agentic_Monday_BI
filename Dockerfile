# Stage 1: Build the React frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

COPY founder_bi_agent/frontend/package*.json ./
RUN npm install

COPY founder_bi_agent/frontend/ ./
RUN npm run build

# Stage 2: Build the FastAPI backend and serve React
FROM python:3.10-slim

WORKDIR /app

# Install backend dependencies explicitly
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bind the underlying monolithic package code
COPY . /app

# Extract the compiled React payload from Stage 1 into the python directory
COPY --from=frontend-builder /app/frontend/dist /app/founder_bi_agent/frontend/dist

# Render implicitly passes the PORT variable, we map FastAPI directly to it
CMD python -m uvicorn founder_bi_agent.backend.api:app --host 0.0.0.0 --port ${PORT:-8000}
