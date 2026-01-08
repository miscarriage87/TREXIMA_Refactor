# TREXIMA - Quick Start Deployment to SAP BTP

## 🎯 Goal
Deploy TREXIMA web application to SAP BTP Cloud Foundry in under 30 minutes.

---

## ✅ Step 1: Verify SAP BTP Access (5 minutes)

### 1.1 Login to SAP BTP Cockpit
- Go to: https://account.hanatrial.ondemand.com/ (for trial) or your enterprise account
- Login with your SAP ID
- Navigate to your **Global Account**

### 1.2 Check Cloud Foundry Setup
- Click on your **Subaccount**
- Verify **Cloud Foundry** is enabled
- Note your:
  - **API Endpoint** (e.g., `https://api.cf.eu10.hana.ondemand.com`)
  - **Org Name** (e.g., `your-org-name`)
  - **Space Name** (e.g., `dev` or `prod`)

### 1.3 Check Quota
- In Subaccount → Overview → Entitlements
- Verify you have:
  - ✅ Application Runtime: At least **512 MB**
  - ✅ Destination service: **1 instance** (lite plan)
  - ✅ Authorization & Trust Management (XSUAA): **1 instance** (application plan)

---

## ✅ Step 2: Install Cloud Foundry CLI (5 minutes)

### macOS
```bash
# Install via Homebrew
brew install cloudfoundry/tap/cf-cli

# Verify installation
cf --version
# Expected: cf version 8.x.x or higher
```

### Windows
```powershell
# Download installer from:
# https://github.com/cloudfoundry/cli/releases

# Or use Chocolatey
choco install cloudfoundry-cli

# Verify
cf --version
```

### Linux (Ubuntu/Debian)
```bash
# Add Cloud Foundry repo
wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
echo "deb https://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list

# Install
sudo apt-get update
sudo apt-get install cf8-cli

# Verify
cf --version
```

---

## ✅ Step 3: Login to Cloud Foundry (2 minutes)

```bash
# Navigate to your project directory
cd "/Users/cpohl/Documents/00 PRIVATE/00 Coding/CLAUDE CODE/TREXIMA"

# Login to Cloud Foundry
cf login

# You'll be prompted for:
# 1. API endpoint (e.g., https://api.cf.eu10.hana.ondemand.com)
# 2. Email
# 3. Password
# 4. Select Org
# 5. Select Space

# Alternative: Login in one command
cf login -a https://api.cf.eu10.hana.ondemand.com -u YOUR_EMAIL -p YOUR_PASSWORD -o YOUR_ORG -s YOUR_SPACE
```

### Verify Login
```bash
cf target
# Should show:
# API endpoint:   https://api.cf.eu10.hana.ondemand.com
# Org:           your-org
# Space:         your-space
```

---

## ✅ Step 4: Quick Deploy (Method A - Fastest) (5 minutes)

### Option 1: Deploy with Default Settings
```bash
# Simple push
cf push trexima-web

# This will:
# - Upload all files (respects .cfignore)
# - Use manifest.yml for configuration
# - Assign a random route
# - Start the application
```

### Option 2: Deploy with Custom Route
```bash
# Deploy with specific subdomain
cf push trexima-web --random-route

# Or with custom hostname
cf push trexima-web --hostname my-trexima
```

### Monitor Deployment
```bash
# Watch the deployment logs
cf logs trexima-web

# In another terminal, check status
watch -n 2 "cf app trexima-web"
```

---

## ✅ Step 5: Verify Deployment (2 minutes)

### Check Application Status
```bash
# Get app information
cf app trexima-web

# Should show:
# state:     running
# instances: 1/1
# routes:    trexima-web-<random>.cfapps.eu10.hana.ondemand.com
```

### Access Your Application
```bash
# Get the URL
cf app trexima-web | grep routes

# Open in browser
# https://trexima-web-<random>.cfapps.eu10.hana.ondemand.com
```

### Test Basic Functionality
1. Open the URL in your browser
2. You should see the TREXIMA home page
3. Try navigating to Export/Import pages

---

## ✅ Step 6: Configure SuccessFactors Connection (5 minutes)

### Method A: Using Environment Variables (Quick Test)
```bash
# Set SuccessFactors API credentials
cf set-env trexima-web ODATA_URL "https://apisalesdemo2.successfactors.eu/odata/v2"
cf set-env trexima-web COMPANY_ID "SFCPART000377"
cf set-env trexima-web API_USERNAME "TREXIMA"
cf set-env trexima-web API_PASSWORD "Trexima@2024"

# Restart app to apply changes
cf restage trexima-web

# This takes 2-3 minutes
```

### Method B: Using Destination Service (Production - See Full Guide)
For production deployments, follow the Destination service setup in DEPLOYMENT_BTP.md

---

## ✅ Step 7: Test End-to-End (5 minutes)

### Upload Test File
1. Go to your TREXIMA URL
2. Click **Export**
3. Upload one of the test XML files from your repository
4. Select languages (e.g., en_US, de_DE)
5. Click **Export**
6. Verify Excel file is generated and downloads

### Check Logs
```bash
# View real-time logs
cf logs trexima-web

# View recent logs
cf logs trexima-web --recent
```

---

## 🎉 Success! Your Application is Live

**Your TREXIMA application is now running on SAP BTP!**

🌐 **URL**: Check with `cf app trexima-web`

---

## 🔧 Common Issues & Quick Fixes

### Issue 1: Deployment Fails - "Insufficient Resources"
```bash
# Check your quota
cf quotas

# Request more quota from your BTP administrator
# Or scale down the app
cf push trexima-web -m 256M
```

### Issue 2: App Crashes After Start
```bash
# Check logs for errors
cf logs trexima-web --recent

# Common causes:
# 1. Missing dependencies - check requirements_new.txt
# 2. Port binding - verify run_web.py uses $PORT
# 3. Python version - check runtime.txt matches
```

### Issue 3: Cannot Access Application
```bash
# Check if app is running
cf apps

# Check routes
cf routes

# Map a new route if needed
cf map-route trexima-web cfapps.eu10.hana.ondemand.com --hostname my-trexima
```

### Issue 4: Upload Files Fail
```bash
# Increase disk quota
cf scale trexima-web -k 2G

# Increase memory
cf scale trexima-web -m 1G

# Restart
cf restart trexima-web
```

---

## 📊 Useful Commands Reference

### Viewing Application Info
```bash
cf app trexima-web              # App details
cf apps                         # All apps
cf env trexima-web              # Environment variables
cf services                     # Bound services
```

### Managing the Application
```bash
cf start trexima-web            # Start app
cf stop trexima-web             # Stop app
cf restart trexima-web          # Restart app
cf restage trexima-web          # Re-stage app (rebuild)
```

### Scaling
```bash
cf scale trexima-web -i 2       # Scale to 2 instances
cf scale trexima-web -m 1G      # Increase memory to 1GB
cf scale trexima-web -k 2G      # Increase disk to 2GB
```

### Logs & Debugging
```bash
cf logs trexima-web             # Stream logs
cf logs trexima-web --recent    # Recent logs
cf events trexima-web           # App events
```

### Cleanup
```bash
cf delete trexima-web           # Delete app
cf delete-service trexima-dest  # Delete service
```

---

## 🚀 Next Steps After Successful Deployment

### 1. Secure Your Application
- [ ] Change default SECRET_KEY: `cf set-env trexima-web SECRET_KEY "your-random-key"`
- [ ] Set up XSUAA authentication (see DEPLOYMENT_BTP.md)
- [ ] Use Destination service for SF credentials (see DEPLOYMENT_BTP.md)

### 2. Production Configuration
- [ ] Enable HTTPS only
- [ ] Configure custom domain
- [ ] Set up monitoring and alerting
- [ ] Implement backup strategy

### 3. Optimize Performance
- [ ] Enable application logging service
- [ ] Set up auto-scaling
- [ ] Configure CDN for static assets
- [ ] Monitor memory and CPU usage

### 4. Set Up CI/CD
- [ ] Configure GitHub Actions (see DEPLOYMENT_BTP.md)
- [ ] Set up automated testing
- [ ] Implement blue-green deployment

---

## 📚 Additional Resources

- **Full Deployment Guide**: `DEPLOYMENT_BTP.md`
- **Cloud Foundry Docs**: https://docs.cloudfoundry.org/
- **SAP BTP Docs**: https://help.sap.com/docs/BTP
- **CF CLI Reference**: https://cli.cloudfoundry.org/

---

## 💡 Pro Tips

1. **Use cf push --strategy rolling** for zero-downtime deployments
2. **Set up health checks**: `cf set-health-check trexima-web http --endpoint /`
3. **Monitor quotas**: `cf quota YOUR_QUOTA_NAME`
4. **Use manifest.yml** for consistent deployments across environments
5. **Tag releases**: Create git tags for production deployments

---

## 🆘 Need Help?

### Check Status
```bash
cf app trexima-web
cf logs trexima-web --recent
```

### Debug Issues
1. Check logs: `cf logs trexima-web --recent`
2. Verify environment: `cf env trexima-web`
3. Check services: `cf services`
4. Review quota: `cf quotas`

### Common Support Channels
- SAP Community: https://community.sap.com/
- Stack Overflow: Tag `sap-cloud-platform`
- GitHub Issues: https://github.com/miscarriage87/TREXIMA_Refactor/issues

---

**🎉 Congratulations! You've successfully deployed TREXIMA to SAP BTP!**
