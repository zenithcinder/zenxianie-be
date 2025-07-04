#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting test environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Warning: .env file not found. Using default test environment variables.${NC}"
else
    echo "📄 Loading environment variables from .env file..."
    export $(cat ../.env | grep -v '^#' | xargs)
fi

# Set Docker Compose project name
export DOCKER_COMPOSE_TEST_NAME="zenxianie-test-$(date +%s)"

# Build and start the containers
echo "📦 Building and starting containers..."
docker-compose -f docker/app.test.yml up --build --abort-on-container-exit

# Check the exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
else
    echo -e "${RED}❌ Some tests failed${NC}"
    exit 1
fi

# Clean up
echo "🧹 Cleaning up..."
docker-compose -f docker/app.test.yml down -v --rmi all --remove-orphans
docker system prune -f --volumes

echo "✨ Done!" 