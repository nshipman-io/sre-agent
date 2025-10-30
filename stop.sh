#!/bin/bash

# SRE AI Agent - Stop Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════╗"
echo "║     Stopping SRE AI Agent...          ║"
echo "╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Ask if user wants to remove volumes
echo ""
echo -e "${YELLOW}Do you want to remove data volumes?${NC}"
echo "This will delete:"
echo "  - ChromaDB indexed documents"
echo "  - All vector embeddings"
echo ""
read -p "Remove volumes? (y/N) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${BLUE}Stopping services and removing volumes...${NC}"
    docker-compose down -v
    echo -e "${GREEN}✓ Services stopped and volumes removed${NC}"
else
    echo -e "${BLUE}Stopping services (keeping volumes)...${NC}"
    docker-compose down
    echo -e "${GREEN}✓ Services stopped (data preserved)${NC}"
fi

echo ""
echo "To start again, run: ./start.sh"
