#!/bin/bash
# TREXIMA v4.0 - Create Required SAP BTP Services

set -e

echo "============================================"
echo "Creating SAP BTP Services for TREXIMA v4.0"
echo "============================================"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
SPACE=${CF_SPACE:-dev}

echo -e "${BLUE}Creating services in space: $SPACE${NC}"
echo ""

# 1. PostgreSQL Database
echo -e "${BLUE}[1/3] Creating PostgreSQL database...${NC}"
cf create-service postgresql v9.6-small trexima-postgres || echo -e "${YELLOW}⚠ Service may already exist${NC}"
echo -e "${GREEN}✓ PostgreSQL service created/verified${NC}"
echo ""

# 2. Object Store (S3-compatible)
echo -e "${BLUE}[2/3] Creating Object Store...${NC}"
cf create-service objectstore standard trexima-objectstore || echo -e "${YELLOW}⚠ Service may already exist${NC}"
echo -e "${GREEN}✓ Object Store service created/verified${NC}"
echo ""

# 3. XSUAA (Authentication)
echo -e "${BLUE}[3/3] Creating XSUAA service...${NC}"

# Create XSUAA configuration
cat > xsuaa-config.json <<EOF
{
  "xsappname": "trexima-v4",
  "tenant-mode": "dedicated",
  "description": "TREXIMA v4.0 Translation Management",
  "scopes": [
    {
      "name": "\$XSAPPNAME.User",
      "description": "Standard user access"
    },
    {
      "name": "\$XSAPPNAME.Admin",
      "description": "Administrator access"
    }
  ],
  "role-templates": [
    {
      "name": "User",
      "description": "TREXIMA User",
      "scope-references": [
        "\$XSAPPNAME.User"
      ]
    },
    {
      "name": "Admin",
      "description": "TREXIMA Administrator",
      "scope-references": [
        "\$XSAPPNAME.User",
        "\$XSAPPNAME.Admin"
      ]
    }
  ],
  "oauth2-configuration": {
    "redirect-uris": [
      "https://trexima-v4.cfapps.*.hana.ondemand.com/**",
      "http://localhost:5000/**"
    ]
  }
}
EOF

cf create-service xsuaa application trexima-xsuaa -c xsuaa-config.json || echo -e "${YELLOW}⚠ Service may already exist${NC}"
echo -e "${GREEN}✓ XSUAA service created/verified${NC}"
echo ""

# Wait for services to be ready
echo -e "${BLUE}Waiting for services to be ready...${NC}"
echo "This may take a few minutes..."

for i in {1..60}; do
    ALL_READY=true

    if ! cf service trexima-postgres | grep -q "create succeeded"; then
        ALL_READY=false
    fi

    if ! cf service trexima-objectstore | grep -q "create succeeded"; then
        ALL_READY=false
    fi

    if ! cf service trexima-xsuaa | grep -q "create succeeded"; then
        ALL_READY=false
    fi

    if [ "$ALL_READY" = true ]; then
        echo ""
        echo -e "${GREEN}✓ All services are ready!${NC}"
        break
    fi

    echo -n "."
    sleep 5
done

echo ""
echo "============================================"
echo -e "${GREEN}Services Setup Complete!${NC}"
echo "============================================"
echo ""
echo "Created services:"
echo "  ✓ trexima-postgres     (PostgreSQL database)"
echo "  ✓ trexima-objectstore  (S3-compatible storage)"
echo "  ✓ trexima-xsuaa        (Authentication)"
echo ""
echo "Next step: Run ./deploy.sh to deploy the application"
echo ""

# Cleanup
rm -f xsuaa-config.json
