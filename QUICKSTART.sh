#!/usr/bin/env bash
# Quick Start Guide for AI Agent System

echo "🚀 AI Agent System - Quick Start Setup"
echo "======================================"
echo ""

# Check Python version
echo "✓ Checking Python environment..."
python --version || { echo "❌ Python not found"; exit 1; }

# Check Node version
echo "✓ Checking Node.js environment..."
node --version || { echo "❌ Node.js not found"; exit 1; }

# Install Python dependencies
echo ""
echo "📦 Installing Python dependencies..."
pip install --upgrade pip
pip install redis websockets

# Install node dependencies (if needed)
echo ""
echo "📦 Installing frontend dependencies..."
cd founder_bi_agent/frontend || exit 1
npm install
cd ../.. || exit 1

# Create .env file template
echo ""
echo "⚙️  Creating environment file template..."
cat > .env.example << 'EOF'
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# PostgreSQL Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=founder_bi
DB_USER=postgres
DB_PASSWORD=

# LLM Configuration
LLM_PROVIDER=gemini
GEMINI_API_KEY=
GROQ_API_KEY=

# WebSocket Configuration
WS_HOST=localhost
WS_PORT=8000
WS_SESSION_TTL=86400

# Frontend
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
EOF

echo "✓ Created .env.example"

# Start Redis (if available)
echo ""
echo "🔴 Redis Setup:"
echo "  Option 1: Docker"
echo "    docker run -d -p 6379:6379 redis:latest"
echo "  Option 2: Local installation"
echo "    brew install redis  # macOS"
echo "    sudo apt-get install redis-server  # Linux"
echo ""

# Setup instructions
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Copy .env.example to .env and update values"
echo "   cp .env.example .env"
echo ""
echo "2. Start Redis:"
echo "   redis-server"
echo ""
echo "3. Start Backend:"
echo "   cd founder_bi_agent/backend"
echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "4. Start Frontend (in new terminal):"
echo "   cd founder_bi_agent/frontend"
echo "   npm run dev"
echo ""
echo "5. Open Browser:"
echo "   http://localhost:3000"
echo ""
echo "6. Test WebSocket Connection:"
echo "   wscat -c ws://localhost:8000/ws/execute/test-session"
echo ""
echo "✅ Setup complete!"
