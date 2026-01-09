#!/bin/bash
# TREXIMA v4.0 - Deployment Script for SAP BTP Cloud Foundry

set -e
echo "============================================"
echo "TREXIMA v4.0 Deployment to SAP BTP"
echo "============================================"
echo ""

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SPACE=${CF_SPACE:-dev}
ORG=${CF_ORG:-}
API_ENDPOINT=${CF_API:-https://api.cf.eu10.hana.ondemand.com}

echo -e "${BLUE}[1/8] Checking prerequisites...${NC}"
if ! command -v cf &> /dev/null; then
    echo -e "${RED}Error: Cloud Foundry CLI not found.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Prerequisites check passed${NC}"
echo ""

echo -e "${BLUE}[2/8] Logging in to Cloud Foundry...${NC}"
if [ -z "$CF_ORG" ]; then
    read -p "Organization: " ORG
fi
cf login -a "$API_ENDPOINT" -o "$ORG" -s "$SPACE"
echo -e "${GREEN}✓ Logged in${NC}"
echo ""

echo -e "${BLUE}[3/8] Building React frontend...${NC}"
cd trexima-frontend
npm install
npm run build
cd ..
echo -e "${GREEN}✓ Frontend built${NC}"
echo ""

echo -e "${BLUE}[4/8] Preparing static assets...${NC}"
rm -rf trexima/web/static/app
mkdir -p trexima/web/static/app
cp -r trexima-frontend/dist/* trexima/web/static/app/
echo -e "${GREEN}✓ Static assets prepared${NC}"
echo ""

echo -e "${BLUE}[5/8] Checking services...${NC}"
REQUIRED_SERVICES=("trexima-postgres" "trexima-objectstore" "trexima-xsuaa")
for service in "${REQUIRED_SERVICES[@]}"; do
    if ! cf service "$service" &> /dev/null; then
        echo -e "${RED}Error: Service '$service' not found!${NC}"
        echo "Run ./create-services.sh first"
        exit 1
    fi
    echo -e "${GREEN}✓ Service '$service' exists${NC}"
done
echo ""

echo -e "${BLUE}[6/8] Pushing application...${NC}"
cf push -f manifest.yml
echo -e "${GREEN}✓ Application pushed${NC}"
echo ""

echo -e "${BLUE}[7/8] Running database migrations...${NC}"
# Check if migrations directory exists
if [ -d "migrations" ]; then
    cf run-task trexima-v4 "flask db upgrade" --name db-migration
    echo -e "${GREEN}✓ Database migration started${NC}"
else
    echo -e "${YELLOW}⚠ No migrations directory found - database will be initialized on first request${NC}"
fi
echo ""

echo -e "${BLUE}[8/8] Verifying deployment...${NC}"
APP_URL=$(cf app trexima-v4 | grep -oP 'routes:\s+\K\S+' | head -1)
if [ -z "$APP_URL" ]; then
    APP_URL="trexima-v4.cfapps.eu10.hana.ondemand.com"
fi

echo ""
echo "============================================"
echo -e "${GREEN}DEPLOYMENT SUCCESSFUL!${NC}"
echo "============================================"
echo ""
echo "Application URL: https://$APP_URL"
echo "Health Check:    https://$APP_URL/api/health"
echo ""
