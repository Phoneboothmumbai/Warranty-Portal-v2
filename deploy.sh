#!/bin/bash
# ============================================================
# Warranty Portal - Production Deployment Script
# ============================================================
# Usage: ./deploy.sh
# 
# This script will:
# 1. Pull latest code from git
# 2. Install backend dependencies
# 3. Install frontend dependencies
# 4. Build the frontend
# 5. Restart the application service
# ============================================================

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}   Warranty Portal - Deployment Script     ${NC}"
echo -e "${GREEN}============================================${NC}"

# Change to project directory
PROJECT_DIR="/var/www/warranty-portal"
cd "$PROJECT_DIR" || { echo -e "${RED}Error: Project directory not found at $PROJECT_DIR${NC}"; exit 1; }

echo -e "\n${YELLOW}[1/5] Pulling latest code from git...${NC}"
git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "Git pull skipped (not a git repo or no remote)"

echo -e "\n${YELLOW}[2/5] Installing backend dependencies...${NC}"
cd "$PROJECT_DIR/backend"
pip install -r requirements.txt --quiet

echo -e "\n${YELLOW}[3/5] Installing frontend dependencies...${NC}"
cd "$PROJECT_DIR/frontend"
npm install --silent --legacy-peer-deps

echo -e "\n${YELLOW}[4/5] Building frontend...${NC}"
npm run build

echo -e "\n${YELLOW}[5/5] Restarting application service...${NC}"
# Try different service managers
if systemctl is-active --quiet warranty-portal 2>/dev/null; then
    sudo systemctl restart warranty-portal
    echo -e "${GREEN}Service restarted via systemctl${NC}"
elif systemctl is-active --quiet warranty-backend 2>/dev/null; then
    sudo systemctl restart warranty-backend
    sudo systemctl restart warranty-frontend 2>/dev/null || true
    echo -e "${GREEN}Services restarted via systemctl${NC}"
elif command -v pm2 &> /dev/null; then
    pm2 restart all
    echo -e "${GREEN}Services restarted via pm2${NC}"
elif command -v supervisorctl &> /dev/null; then
    sudo supervisorctl restart all
    echo -e "${GREEN}Services restarted via supervisorctl${NC}"
else
    echo -e "${YELLOW}Warning: No service manager found. Please restart your application manually.${NC}"
fi

echo -e "\n${GREEN}============================================${NC}"
echo -e "${GREEN}   Deployment Complete!                    ${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "\nYour application should now be running with the latest changes."
echo -e "If you encounter issues, check your service logs."
