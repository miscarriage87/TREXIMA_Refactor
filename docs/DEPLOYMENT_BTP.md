# TREXIMA - SAP BTP Deployment Guide

This guide covers deploying TREXIMA to SAP Business Technology Platform (BTP) using Cloud Foundry.

## 📋 Prerequisites

### 1. SAP BTP Account
- Active SAP BTP global account
- Cloud Foundry environment enabled
- Subaccount with sufficient quota (512MB RAM minimum)

### 2. Local Tools
```bash
# Install Cloud Foundry CLI
# macOS
brew install cloudfoundry/tap/cf-cli

# Windows
# Download from: https://github.com/cloudfoundry/cli/releases

# Linux
wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
echo "deb https://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
sudo apt-get update
sudo apt-get install cf7-cli

# Verify installation
cf --version
```

### 3. Install MBT (Multi-Target Application Build Tool) - Optional for MTA deployment
```bash
# Install Node.js first (required)
# macOS
brew install node

# Then install MBT
npm install -g mbt
```

## 🚀 Deployment Methods

### Method 1: Simple CF Push (Quickest)

#### Step 1: Login to Cloud Foundry
```bash
# Set CF API endpoint (replace with your region)
cf api https://api.cf.eu10.hana.ondemand.com

# Login
cf login
# Enter email and password when prompted

# Target your org and space
cf target -o YOUR_ORG -s YOUR_SPACE
```

#### Step 2: Deploy Application
```bash
cd /path/to/TREXIMA

# Deploy using manifest.yml
cf push trexima-web -f manifest.yml

# Or deploy with custom settings
cf push trexima-web -m 512M -k 1G --random-route
```

#### Step 3: Access Your Application
```bash
# Get the app URL
cf app trexima-web

# Expected output shows the route, e.g.:
# routes: trexima-web-calm-kudu-xy.cfapps.eu10.hana.ondemand.com
```

### Method 2: MTA Deployment (Recommended for Production)

#### Step 1: Build MTA Archive
```bash
cd /path/to/TREXIMA

# Build the MTA archive
mbt build

# This creates: mta_archives/trexima_1.0.0.mtar
```

#### Step 2: Deploy MTA
```bash
# Login to Cloud Foundry (if not already logged in)
cf login

# Deploy the MTA archive
cf deploy mta_archives/trexima_1.0.0.mtar
```

This will automatically:
- Deploy the application
- Create and bind the Destination service
- Create and bind the XSUAA service
- Configure routes and environment variables

## 🔐 Configure SuccessFactors Connection

### Option A: Using Destination Service (Recommended)

1. **Go to SAP BTP Cockpit**
   - Navigate to your subaccount
   - Go to Connectivity → Destinations

2. **Create Destination**
   ```
   Name: SFSF_API
   Type: HTTP
   URL: https://apisalesdemo2.successfactors.eu/odata/v2
   Proxy Type: Internet
   Authentication: OAuth2SAMLBearerAssertion

   Additional Properties:
   - audience: https://api2.successfactors.eu
   - authnContextClassRef: urn:oasis:names:tc:SAML:2.0:ac:classes:PreviousSession
   - tokenServiceURL: https://apisalesdemo2.successfactors.eu/oauth/token
   - companyId: YOUR_COMPANY_ID
   - clientKey: YOUR_CLIENT_KEY
   - tokenServiceUser: YOUR_USER
   - tokenServicePassword: YOUR_PASSWORD
   ```

3. **Bind Destination to Application**
   ```bash
   # If not using MTA, bind manually
   cf bind-service trexima-web trexima-destination
   cf restage trexima-web
   ```

### Option B: Using Environment Variables

```bash
# Set environment variables for direct API access
cf set-env trexima-web ODATA_URL "https://apisalesdemo2.successfactors.eu/odata/v2"
cf set-env trexima-web COMPANY_ID "YOUR_COMPANY_ID"
cf set-env trexima-web API_USERNAME "YOUR_USERNAME"
cf set-env trexima-web API_PASSWORD "YOUR_PASSWORD"

# Restage application
cf restage trexima-web
```

**⚠️ Warning**: Using environment variables is less secure. Use Destination service for production.

## 🔒 Configure Authentication (Optional)

### Enable XSUAA Authentication

1. **The xs-security.json is already configured**

2. **Assign Roles to Users**
   - Go to SAP BTP Cockpit → Security → Role Collections
   - Assign "TREXIMA_Administrator" or "TREXIMA_User" to users

3. **Update Application to Use XSUAA**

   The application will need code changes to integrate XSUAA authentication. This can be done by:
   - Adding `@xssec.check_scope("$XSAPPNAME.User")` decorators to routes
   - Installing xssec library: `pip install sap-xssec`

## 📊 Monitoring & Logs

### View Application Logs
```bash
# Stream logs in real-time
cf logs trexima-web

# View recent logs
cf logs trexima-web --recent

# Get application info
cf app trexima-web
```

### Application Health Check
```bash
# Check if app is running
cf apps

# Get detailed information
cf app trexima-web

# Scale application
cf scale trexima-web -i 2  # Scale to 2 instances
cf scale trexima-web -m 1G # Increase memory to 1GB
```

## 🔧 Environment Configuration

### Key Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Application port | Set by CF |
| `HOST` | Bind address | 0.0.0.0 |
| `FLASK_ENV` | Flask environment | production |
| `SECRET_KEY` | Flask secret key | Auto-generated |
| `ODATA_URL` | SuccessFactors API URL | From Destination |
| `COMPANY_ID` | SF Company ID | From Destination |

### Set Custom Variables
```bash
cf set-env trexima-web SECRET_KEY "your-secure-secret-key-here"
cf set-env trexima-web MAX_UPLOAD_SIZE "104857600"  # 100MB
cf restage trexima-web
```

## 🚦 CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy-btp.yml`:

```yaml
name: Deploy to SAP BTP

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Install Cloud Foundry CLI
        run: |
          wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
          echo "deb https://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
          sudo apt-get update
          sudo apt-get install cf7-cli

      - name: Login to Cloud Foundry
        run: |
          cf api ${{ secrets.CF_API }}
          cf auth ${{ secrets.CF_USERNAME }} ${{ secrets.CF_PASSWORD }}
          cf target -o ${{ secrets.CF_ORG }} -s ${{ secrets.CF_SPACE }}

      - name: Deploy Application
        run: cf push trexima-web -f manifest.yml
```

## 📝 Post-Deployment Checklist

- [ ] Application is accessible via the route
- [ ] API connection to SuccessFactors works
- [ ] File upload functionality works
- [ ] Export generates Excel workbooks correctly
- [ ] Import processes translations successfully
- [ ] Logs are clean (no errors)
- [ ] XSUAA authentication configured (if needed)
- [ ] Destination service bound and working
- [ ] Users have proper role assignments

## 🐛 Troubleshooting

### Application Won't Start
```bash
# Check recent logs
cf logs trexima-web --recent

# Common issues:
# 1. Check Python version matches runtime.txt
# 2. Check requirements_new.txt has all dependencies
# 3. Check PORT environment variable is used correctly
```

### Memory Issues
```bash
# Increase memory allocation
cf scale trexima-web -m 1G
cf restage trexima-web
```

### Cannot Connect to SuccessFactors
```bash
# Verify destination configuration
cf services
cf service trexima-destination

# Check environment variables
cf env trexima-web

# Test API connectivity from logs
cf logs trexima-web
```

### File Upload Fails
```bash
# Increase disk quota
cf scale trexima-web -k 2G

# Check MAX_CONTENT_LENGTH in Flask config
cf set-env trexima-web MAX_UPLOAD_SIZE "209715200"  # 200MB
cf restage trexima-web
```

## 🔄 Update/Rollback

### Update Application
```bash
# Pull latest code
git pull origin main

# Redeploy
cf push trexima-web
```

### Rollback to Previous Version
```bash
# List recent app versions
cf apps --show-package

# Rollback (if supported by your CF version)
cf rollback trexima-web
```

## 📚 Additional Resources

- [SAP BTP Documentation](https://help.sap.com/docs/BTP)
- [Cloud Foundry CLI Reference](https://cli.cloudfoundry.org/en-US/v7/)
- [MTA Development](https://help.sap.com/docs/SAP_HANA_PLATFORM/4505d0bdaf4948449b7f7379d24d0f0d/ba7dd5a47b7a4858a652d15f9673c28d.html)
- [XSUAA Documentation](https://help.sap.com/docs/CP_AUTHORIZ_TRUST_MNG)

## 💡 Tips

1. **Use MTA for production** - Better service management and deployment consistency
2. **Enable Application Logging** - Use Application Logging service for better log management
3. **Set up Auto-Scaling** - Configure auto-scaling for high availability
4. **Use Private Networks** - Consider SAP Private Link for secure connectivity
5. **Implement Health Checks** - Add `/health` endpoint for monitoring

## 🆘 Support

For issues or questions:
1. Check application logs: `cf logs trexima-web --recent`
2. Review SAP BTP Cockpit for service status
3. Open an issue on GitHub: https://github.com/miscarriage87/TREXIMA_Refactor/issues
