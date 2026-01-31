#!/bin/bash
# Deployment script for Warranty Portal
# Run this on your Vultr server

set -e

echo "🚀 Starting deployment..."

# Navigate to project directory
cd /var/www/warranty-portal

# Pull latest code
echo "📥 Pulling latest code..."
git fetch origin
git reset --hard origin/main

# Copy production env if not exists
if [ ! -f .env ]; then
    cp .env.production .env
    echo "⚠️  Created .env from .env.production - Please update JWT_SECRET!"
fi

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose down || true

# Clean up Docker
echo "🧹 Cleaning Docker cache..."
docker system prune -f

# Build and start
echo "🔨 Building containers..."
docker-compose build --no-cache

echo "▶️  Starting services..."
docker-compose up -d

# Wait for services to start
echo "⏳ Waiting for services to initialize..."
sleep 15

# Show status
echo "📊 Container status:"
docker-compose ps

echo ""
echo "📜 Frontend logs (last 30 lines):"
docker-compose logs --tail=30 frontend

echo ""
echo "✅ Deployment complete!"
echo "🌐 Visit https://aftersales.support to verify"
