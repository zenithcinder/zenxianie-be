#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Generating requirements.txt from Pipfile.lock${NC}"
echo "# Generated from Pipfile.lock - Do not edit directly" > requirements.txt
pipenv lock -r >> requirements.txt

echo -e "${GREEN}✅ requirements.txt has been updated from Pipfile.lock${NC}"
echo "You can now use this file for tools that don't support Pipenv directly."
