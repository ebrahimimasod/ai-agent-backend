#!/bin/bash

# Simple Deployment Script - Force pull from remote
# This script forcefully syncs with remote and restarts Docker services

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Starting Deployment${NC}"
echo -e "${GREEN}========================================${NC}"

# Check docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    exit 1
fi

# Get current branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "\n${YELLOW}[1/4] Syncing with remote (branch: $CURRENT_BRANCH)...${NC}"

# Fetch latest changes
git fetch origin

# Force reset to remote branch (discard all local changes)
git reset --hard origin/$CURRENT_BRANCH

echo -e "${GREEN}✓ Code synced with remote${NC}"

# Check .env
echo -e "\n${YELLOW}[2/4] Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${YELLOW}Created .env from example. Please edit it and run again.${NC}"
        exit 1
    fi
    exit 1
fi
echo -e "${GREEN}✓ .env file exists${NC}"

# Restart Docker services
echo -e "\n${YELLOW}[3/4] Restarting Docker services...${NC}"
docker compose down
docker compose build --no-cache
docker compose up -d
echo -e "${GREEN}✓ Services restarted${NC}"

# Check status
echo -e "\n${YELLOW}[4/4] Checking status...${NC}"
sleep 5
docker compose ps

# Health check
echo -e "\n${YELLOW}Checking API health...${NC}"
sleep 10
if command -v curl &> /dev/null; then
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
    if [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✓ API is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ API returned HTTP $HTTP_CODE${NC}"
    fi
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "\nAPI: ${GREEN}http://localhost:8001/docs${NC}"
