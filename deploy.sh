#!/bin/bash

# Automated Deployment Script
# This script pulls the latest code from Git and restarts Docker services

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   Starting Deployment Process${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if we're in the correct directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found!${NC}"
    echo -e "${RED}Please run this script from the project root directory.${NC}"
    exit 1
fi

# Step 1: Pull latest changes from Git
echo -e "\n${YELLOW}[1/5] Pulling latest changes from Git...${NC}"
git fetch origin
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo -e "Current branch: ${GREEN}$CURRENT_BRANCH${NC}"

# Check for local changes
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}Warning: You have uncommitted local changes${NC}"
    read -p "Do you want to discard local changes and pull? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git reset --hard HEAD
        echo -e "${GREEN}✓ Local changes reset${NC}"
    else
        echo -e "${RED}Deployment cancelled${NC}"
        exit 1
    fi
fi

git pull origin $CURRENT_BRANCH
echo -e "${GREEN}✓ Code updated successfully${NC}"

# Step 2: Check .env file
echo -e "\n${YELLOW}[2/5] Checking .env file...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}Do you want to copy from .env.example? (y/n): ${NC}"
        read -p "" -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            cp .env.example .env
            echo -e "${GREEN}✓ .env file created. Please edit it and run deploy again${NC}"
            exit 1
        else
            exit 1
        fi
    else
        exit 1
    fi
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Step 3: Stop previous services
echo -e "\n${YELLOW}[3/5] Stopping previous services...${NC}"
docker compose down
echo -e "${GREEN}✓ Services stopped${NC}"

# Step 4: Build and start new services
echo -e "\n${YELLOW}[4/5] Building and starting new services...${NC}"
docker compose build --no-cache
docker compose up -d
echo -e "${GREEN}✓ Services started successfully${NC}"

# Step 5: Check service status
echo -e "\n${YELLOW}[5/5] Checking service status...${NC}"
sleep 5  # Wait for services to start

echo -e "\n${GREEN}Container Status:${NC}"
docker compose ps

# Check health endpoint
echo -e "\n${YELLOW}Checking Health Endpoint...${NC}"
sleep 10  # Wait for API to be ready

if command -v curl &> /dev/null; then
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8001/health || echo "000")
    if [ "$HEALTH_CHECK" = "200" ]; then
        echo -e "${GREEN}✓ API is healthy and running${NC}"
    else
        echo -e "${YELLOW}⚠ API is not ready yet (HTTP $HEALTH_CHECK)${NC}"
        echo -e "${YELLOW}Please wait a moment and check the logs${NC}"
    fi
else
    echo -e "${YELLOW}curl not installed, health check skipped${NC}"
fi

# Show recent logs
echo -e "\n${YELLOW}Recent API Logs:${NC}"
docker compose logs --tail=20 api

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}   Deployment Completed Successfully! ✓${NC}"
echo -e "${GREEN}========================================${NC}"

echo -e "\n${YELLOW}Useful Commands:${NC}"
echo -e "  • View logs:           ${GREEN}docker compose logs -f${NC}"
echo -e "  • View API logs:       ${GREEN}docker compose logs -f api${NC}"
echo -e "  • View Worker logs:    ${GREEN}docker compose logs -f worker${NC}"
echo -e "  • Service status:      ${GREEN}docker compose ps${NC}"
echo -e "  • Restart services:    ${GREEN}docker compose restart${NC}"
echo -e "  • Stop services:       ${GREEN}docker compose down${NC}"

echo -e "\n${YELLOW}API is available at:${NC}"
echo -e "  • Health: ${GREEN}http://localhost:8001/health${NC}"
echo -e "  • Docs:   ${GREEN}http://localhost:8001/docs${NC}"
