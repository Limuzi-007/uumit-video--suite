#!/bin/bash
# ─── UUMit Video Suite - Deploy Script ─────────────────────────────
# Usage: bash scripts/deploy.sh
set -euo pipefail

echo "========================================"
echo "  UUMit Video Suite - Deploy"
echo "========================================"

# Check dependencies
command -v docker >/dev/null 2>&1 || { echo "❌ Docker not found. Install: https://docs.docker.com/get-docker/"; exit 1; }
command -v git >/dev/null 2>&1 || { echo "❌ Git not found"; exit 1; }

# Load env
if [ ! -f .env ]; then
    echo "📝 Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Edit .env and set your API_KEYS before production use!"
fi

# Pull latest (if git repo)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "📦 Updating from git..."
    git pull --rebase
fi

# Build and run
echo "🐳 Building Docker image..."
docker compose build --no-cache

echo "🚀 Starting services..."
docker compose up -d

echo ""
echo "✅ Deployed!"
echo "   Health: http://localhost:8000/health"
echo "   Docs:   http://localhost:8000/docs"
echo ""
echo "📊 Check logs: docker compose logs -f"
