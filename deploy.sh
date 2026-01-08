#!/bin/bash
# TREXIMA BTP Deployment Script
# Quick deployment helper for SAP BTP Cloud Foundry

set -e

echo "=========================================="
echo "  TREXIMA - SAP BTP Deployment Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if CF CLI is installed
echo "Step 1: Checking prerequisites..."
if ! command -v cf &> /dev/null; then
    print_error "Cloud Foundry CLI not found!"
    echo ""
    echo "Please install CF CLI:"
    echo "  macOS:   brew install cloudfoundry/tap/cf-cli"
    echo "  Windows: https://github.com/cloudfoundry/cli/releases"
    echo "  Linux:   See DEPLOYMENT_QUICKSTART.md"
    exit 1
fi

cf_version=$(cf --version)
print_success "Cloud Foundry CLI installed: $cf_version"

# Check if logged in
echo ""
echo "Step 2: Checking CF login status..."
if ! cf target &> /dev/null; then
    print_error "Not logged in to Cloud Foundry"
    echo ""
    echo "Please login first:"
    echo "  cf login"
    echo ""
    echo "Or use:"
    echo "  cf login -a https://api.cf.eu10.hana.ondemand.com"
    exit 1
fi

target_info=$(cf target)
print_success "Logged in to Cloud Foundry"
echo "$target_info"

# Confirm deployment
echo ""
echo "Step 3: Ready to deploy..."
print_info "This will deploy TREXIMA to SAP BTP Cloud Foundry"
echo ""
read -p "Continue with deployment? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Check if app already exists
echo ""
echo "Step 4: Checking for existing deployment..."
if cf app trexima-web &> /dev/null; then
    print_info "App 'trexima-web' already exists"
    echo ""
    read -p "Update existing app? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Deployment cancelled."
        exit 0
    fi
    ACTION="update"
else
    print_info "This will be a new deployment"
    ACTION="new"
fi

# Deploy application
echo ""
echo "Step 5: Deploying application..."
print_info "This may take 2-3 minutes..."
echo ""

if cf push trexima-web -f manifest.yml; then
    print_success "Application deployed successfully!"
else
    print_error "Deployment failed!"
    echo ""
    echo "Check logs with:"
    echo "  cf logs trexima-web --recent"
    exit 1
fi

# Get app info
echo ""
echo "Step 6: Getting application information..."
echo ""
cf app trexima-web

# Get the route
APP_ROUTE=$(cf app trexima-web | grep routes: | awk '{print $2}')

echo ""
echo "=========================================="
print_success "Deployment Complete!"
echo "=========================================="
echo ""
echo "Your application is now running at:"
echo "  https://$APP_ROUTE"
echo ""
echo "Useful commands:"
echo "  View logs:    cf logs trexima-web"
echo "  Check status: cf app trexima-web"
echo "  Restart app:  cf restart trexima-web"
echo ""
echo "Next steps:"
echo "  1. Open the app URL in your browser"
echo "  2. Configure SF credentials (see DEPLOYMENT_QUICKSTART.md)"
echo "  3. Test export/import functionality"
echo ""
print_info "For detailed configuration, see DEPLOYMENT_BTP.md"
echo ""
