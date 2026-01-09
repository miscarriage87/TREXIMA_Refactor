#!/bin/bash
#
# TREXIMA v4.0 - Deployment Script
#
# This script:
# 1. Builds the frontend
# 2. Copies build to Flask static folder
# 3. Runs pre-deployment tests
# 4. Deploys to Cloud Foundry
# 5. Runs post-deployment tests
#
# Usage:
#   ./scripts/deploy.sh        # Full deployment with tests
#   ./scripts/deploy.sh --skip-tests  # Deploy without tests
#   ./scripts/deploy.sh --test-only   # Run tests without deploying

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Change to project root
cd "$PROJECT_ROOT"

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  TREXIMA v4.0 Deployment${NC}"
echo -e "${YELLOW}========================================${NC}"

# Parse arguments
SKIP_TESTS=false
TEST_ONLY=false

while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-tests) SKIP_TESTS=true ;;
        --test-only) TEST_ONLY=true ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
    shift
done

# Step 1: Build Frontend
build_frontend() {
    echo -e "\n${GREEN}[1/5] Building frontend...${NC}"

    cd "$PROJECT_ROOT/trexima-frontend"

    if [ ! -d "node_modules" ]; then
        echo "Installing npm dependencies..."
        npm install
    fi

    echo "Running build..."
    npm run build

    if [ ! -f "dist/index.html" ]; then
        echo -e "${RED}ERROR: Frontend build failed - dist/index.html not found${NC}"
        exit 1
    fi

    echo -e "${GREEN}Frontend build successful${NC}"
    cd "$PROJECT_ROOT"
}

# Step 2: Copy build to Flask static
copy_build() {
    echo -e "\n${GREEN}[2/5] Copying frontend build to Flask static folder...${NC}"

    STATIC_APP_DIR="$PROJECT_ROOT/trexima/web/static/app"

    # Remove old build
    rm -rf "$STATIC_APP_DIR"

    # Copy new build
    cp -r "$PROJECT_ROOT/trexima-frontend/dist" "$STATIC_APP_DIR"

    if [ ! -f "$STATIC_APP_DIR/index.html" ]; then
        echo -e "${RED}ERROR: Failed to copy frontend build${NC}"
        exit 1
    fi

    echo "Contents of static/app:"
    ls -la "$STATIC_APP_DIR"
    echo ""

    echo -e "${GREEN}Frontend build copied successfully${NC}"
}

# Step 3: Pre-deployment tests
run_pre_tests() {
    echo -e "\n${GREEN}[3/5] Running pre-deployment tests...${NC}"

    python3 "$PROJECT_ROOT/tests/test_deployment.py" --check-build

    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Pre-deployment tests failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}Pre-deployment tests passed${NC}"
}

# Step 4: Deploy to Cloud Foundry
deploy_cf() {
    echo -e "\n${GREEN}[4/5] Deploying to Cloud Foundry...${NC}"

    # Check if logged in
    if ! cf target > /dev/null 2>&1; then
        echo -e "${RED}ERROR: Not logged in to Cloud Foundry${NC}"
        echo "Please run: cf login"
        exit 1
    fi

    # Deploy
    cf push

    if [ $? -ne 0 ]; then
        echo -e "${RED}ERROR: Deployment failed${NC}"
        exit 1
    fi

    echo -e "${GREEN}Deployment successful${NC}"
}

# Step 5: Post-deployment tests
run_post_tests() {
    echo -e "\n${GREEN}[5/5] Running post-deployment tests...${NC}"

    # Wait for app to stabilize
    echo "Waiting 10 seconds for app to stabilize..."
    sleep 10

    python3 "$PROJECT_ROOT/tests/test_deployment.py" --prod

    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}WARNING: Post-deployment tests failed${NC}"
        echo "Please check the deployment manually"
        return 1
    fi

    echo -e "${GREEN}Post-deployment tests passed${NC}"
}

# Main execution
if [ "$TEST_ONLY" = true ]; then
    echo "Running tests only..."
    python3 "$PROJECT_ROOT/tests/test_deployment.py" --check-build --prod
    exit $?
fi

build_frontend
copy_build

if [ "$SKIP_TESTS" = false ]; then
    run_pre_tests
fi

deploy_cf

if [ "$SKIP_TESTS" = false ]; then
    run_post_tests
fi

echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "URL: https://trexima-v4.cfapps.eu10-004.hana.ondemand.com"
