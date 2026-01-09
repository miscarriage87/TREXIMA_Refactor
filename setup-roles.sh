#!/bin/bash
# TREXIMA Role Collection Setup Script
# This script uses the XSUAA REST API to create role collections

set -e

echo "================================================"
echo "TREXIMA Role Collection Setup"
echo "================================================"
echo ""

# Configuration
XSUAA_URL="https://hrisbtpsubaccount-yzr6xc10.authentication.eu10.hana.ondemand.com"
API_URL="https://api.authentication.eu10.hana.ondemand.com"
CLIENT_ID="sb-na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248"
CLIENT_SECRET="466f5872-0f53-45db-984a-5b5315403792\$RPa-vzmHEQEnLx6iwsupPeL2qgH5-CLqJH3tYNlsEfw="
APP_ID="na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248"

echo "Step 1: Getting OAuth2 token..."
TOKEN_RESPONSE=$(curl -s -X POST "${XSUAA_URL}/oauth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -u "${CLIENT_ID}:${CLIENT_SECRET}" \
  -d "grant_type=client_credentials")

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    echo "Response: $TOKEN_RESPONSE"
    exit 1
fi

echo "✅ Token acquired"
echo ""

# Create TREXIMA User Role Collection
echo "Step 2: Creating TREXIMA_User role collection..."

USER_ROLE_COLLECTION=$(cat <<EOF
{
  "name": "TREXIMA_User",
  "description": "Standard users for TREXIMA translation management",
  "roleReferences": [
    {
      "roleTemplateAppId": "${APP_ID}",
      "roleTemplateName": "User",
      "name": "User"
    }
  ]
}
EOF
)

curl -s -X POST "${API_URL}/sap/rest/authorization/v2/rolecollections" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$USER_ROLE_COLLECTION" && echo "✅ TREXIMA_User role collection created" || echo "⚠️  May already exist"

echo ""

# Create TREXIMA Admin Role Collection
echo "Step 3: Creating TREXIMA_Admin role collection..."

ADMIN_ROLE_COLLECTION=$(cat <<EOF
{
  "name": "TREXIMA_Admin",
  "description": "Administrators for TREXIMA with full permissions",
  "roleReferences": [
    {
      "roleTemplateAppId": "${APP_ID}",
      "roleTemplateName": "User",
      "name": "User"
    },
    {
      "roleTemplateAppId": "${APP_ID}",
      "roleTemplateName": "Admin",
      "name": "Admin"
    }
  ]
}
EOF
)

curl -s -X POST "${API_URL}/sap/rest/authorization/v2/rolecollections" \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "$ADMIN_ROLE_COLLECTION" && echo "✅ TREXIMA_Admin role collection created" || echo "⚠️  May already exist"

echo ""
echo "================================================"
echo "✅ Role Collections Setup Complete!"
echo "================================================"
echo ""
echo "Created role collections:"
echo "  • TREXIMA_User  - Standard user access"
echo "  • TREXIMA_Admin - Full administrator access"
echo ""
echo "Next steps:"
echo "1. Go to SAP BTP Cockpit → Security → Role Collections"
echo "2. Assign users to the role collections"
echo "3. Users can now access: https://trexima-v4.cfapps.eu10-004.hana.ondemand.com"
echo ""
