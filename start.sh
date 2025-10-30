#!/bin/bash

# SRE AI Agent - Quick Start Script
# This script helps you get the SRE AI Agent up and running quickly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════╗"
echo "║      SRE AI Agent - Quick Start       ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Check for Docker
echo -e "${BLUE}Checking prerequisites...${NC}"
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker not found${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
else
    echo -e "${GREEN}✓ Docker found${NC}"
fi

# Check for Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose not found${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
else
    echo -e "${GREEN}✓ Docker Compose found${NC}"
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Creating .env from template..."
    cp .env.docker.example .env

    echo ""
    echo -e "${YELLOW}⚠ ACTION REQUIRED:${NC}"
    echo "Please edit the .env file and add your OpenAI API key:"
    echo ""
    echo "  OPENAI_API_KEY=sk-your-actual-key-here"
    echo ""
    read -p "Press Enter once you've updated the .env file..."
fi

# Check if OPENAI_API_KEY is set in .env
if ! grep -q "^OPENAI_API_KEY=sk-" .env 2>/dev/null; then
    echo -e "${RED}✗ OPENAI_API_KEY not configured in .env${NC}"
    echo "Please edit .env and set your OpenAI API key"
    exit 1
else
    echo -e "${GREEN}✓ OpenAI API key configured${NC}"
fi

# Check for kubeconfig
if [ ! -f "$HOME/.kube/config" ]; then
    echo -e "${YELLOW}⚠ No kubeconfig found at $HOME/.kube/config${NC}"
    echo "Make sure you have access to a Kubernetes cluster"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo -e "${GREEN}✓ Kubeconfig found${NC}"
fi

echo ""
echo -e "${BLUE}Starting services...${NC}"

# Stop any existing containers
docker-compose down 2>/dev/null || true

# Build and start services
echo "Building Docker images (this may take a few minutes)..."
docker-compose up -d --build

# Wait for services to be healthy
echo ""
echo -e "${BLUE}Waiting for services to start...${NC}"

MAX_WAIT=60
ELAPSED=0

while [ $ELAPSED -lt $MAX_WAIT ]; do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Backend is ready${NC}"
        break
    fi
    echo -n "."
    sleep 2
    ELAPSED=$((ELAPSED + 2))
done

if [ $ELAPSED -ge $MAX_WAIT ]; then
    echo -e "${RED}✗ Backend failed to start${NC}"
    echo "Check logs with: docker-compose logs backend"
    exit 1
fi

sleep 2

if curl -sf http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Frontend is ready${NC}"
else
    echo -e "${YELLOW}⚠ Frontend may still be starting${NC}"
fi

# Index runbooks
echo ""
echo -e "${BLUE}Indexing runbooks...${NC}"
if curl -sf -X POST http://localhost:8000/v1/docs/index-directory \
    -H "Content-Type: application/json" \
    -d '{"directory_path": "/app/docs/runbooks"}' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Runbooks indexed${NC}"
else
    echo -e "${YELLOW}⚠ Failed to index runbooks (you can do this manually later)${NC}"
fi

# Success message
echo ""
echo -e "${GREEN}"
echo "╔═══════════════════════════════════════╗"
echo "║     🎉 SRE AI Agent is running! 🎉    ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Access the application:"
echo ""
echo -e "  ${BLUE}Frontend:${NC}     http://localhost:3000"
echo -e "  ${BLUE}Backend API:${NC}  http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}     http://localhost:8000/docs"
echo ""
echo "Useful commands:"
echo ""
echo -e "  ${BLUE}View logs:${NC}        docker-compose logs -f"
echo -e "  ${BLUE}Stop services:${NC}    docker-compose down"
echo -e "  ${BLUE}Restart:${NC}          docker-compose restart"
echo ""
echo "Try asking the agent:"
echo '  - "Show me all pods in default namespace"'
echo '  - "Why is my pod crashing?"'
echo '  - "How do I fix CrashLoopBackOff?"'
echo ""
echo -e "${GREEN}Happy troubleshooting! 🚀${NC}"
