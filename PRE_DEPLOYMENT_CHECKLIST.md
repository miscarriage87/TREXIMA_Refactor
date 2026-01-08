# TREXIMA - Pre-Deployment Checklist

Use this checklist before deploying to SAP BTP to ensure everything is ready.

---

## ☑️ SAP BTP Account Access

- [ ] I have access to an SAP BTP account (trial or enterprise)
- [ ] I can login to SAP BTP Cockpit: https://account.hanatrial.ondemand.com/
- [ ] I have a subaccount with Cloud Foundry enabled
- [ ] I know my API endpoint (e.g., `https://api.cf.eu10.hana.ondemand.com`)
- [ ] I know my Org name
- [ ] I know my Space name (e.g., `dev` or `prod`)

**Where to find this info:**
- BTP Cockpit → Subaccount → Overview → Cloud Foundry Environment

---

## ☑️ Resource Quota

Check in: BTP Cockpit → Subaccount → Entitlements

- [ ] Application Runtime: **512 MB** available (minimum)
- [ ] Destination service: **1 instance** available (for SF connection)
- [ ] XSUAA service: **1 instance** available (for authentication)

**If quota is insufficient:**
- Request more from your BTP administrator
- Or scale down the app: Edit `manifest.yml` and set `memory: 256M`

---

## ☑️ Local Tools Installed

### Cloud Foundry CLI
- [ ] CF CLI installed (version 7.x or 8.x)

**Test:** Open terminal and run:
```bash
cf --version
```

**Install if needed:**
- macOS: `brew install cloudfoundry/tap/cf-cli`
- Windows: Download from https://github.com/cloudfoundry/cli/releases
- Linux: See DEPLOYMENT_QUICKSTART.md

### Optional: MTA Build Tool (for production MTA deployment)
- [ ] Node.js installed
- [ ] MBT installed: `npm install -g mbt`

**Only needed if using MTA deployment method**

---

## ☑️ SuccessFactors Connection Details

For connecting TREXIMA to SuccessFactors:

- [ ] I have the OData API URL (e.g., `https://apisalesdemo2.successfactors.eu/odata/v2`)
- [ ] I have the Company ID (e.g., `SFCPART000377`)
- [ ] I have API credentials (username/password or OAuth)
- [ ] I know which authentication method to use:
  - [ ] Basic Auth (username/password)
  - [ ] OAuth2 SAML Bearer Assertion

**You'll need this after deployment to configure the connection**

---

## ☑️ Repository & Code

- [ ] Code is up to date from GitHub
- [ ] Latest commit is: `75c2e2a` (or newer)
- [ ] All required files are present:
  - [ ] `manifest.yml`
  - [ ] `runtime.txt`
  - [ ] `Procfile`
  - [ ] `requirements_new.txt`
  - [ ] `trexima/` directory with all modules
  - [ ] `.cfignore`

**Verify:** Run `git status` in your TREXIMA directory

---

## ☑️ Pre-Deployment Configuration

### Review manifest.yml
- [ ] App name is correct: `trexima-web`
- [ ] Memory allocation is appropriate: `512M` (default)
- [ ] Buildpack is correct: `python_buildpack`

### Review runtime.txt
- [ ] Python version specified: `python-3.9.18`

### Review requirements_new.txt
- [ ] All dependencies are listed
- [ ] No version conflicts

---

## ☑️ Security Considerations

- [ ] LoginCredentialsForAPI.txt is in `.gitignore` (should NOT be deployed)
- [ ] `.cfignore` excludes test files and credentials
- [ ] I have a plan for managing SF credentials:
  - [ ] Option A: Environment variables (quick test)
  - [ ] Option B: Destination service (production)

**Verify .cfignore excludes:**
- `LoginCredentialsForAPI.txt`
- `test_*.py`
- Test output directories

---

## ☑️ Deployment Method Selected

Choose ONE method:

### Method A: Quick CF Push (Recommended for First Deployment)
- [ ] I will use: `cf push trexima-web`
- [ ] Duration: ~5 minutes
- [ ] Use when: Testing, development, quick deployment

### Method B: MTA Deployment (Recommended for Production)
- [ ] I will use: `mbt build && cf deploy mta_archives/trexima_1.0.0.mtar`
- [ ] Duration: ~10 minutes
- [ ] Use when: Production, with services (Destination, XSUAA)

**For first-time deployment, use Method A**

---

## ☑️ Post-Deployment Testing Plan

After deployment, I will test:

- [ ] Application is accessible via URL
- [ ] Home page loads correctly
- [ ] Export page is accessible
- [ ] Can upload a test XML file
- [ ] Can select languages
- [ ] Export generates an Excel file
- [ ] Import page is accessible
- [ ] Can upload an Excel file
- [ ] Import processes successfully

---

## ☑️ Support Resources Ready

- [ ] I have bookmarked DEPLOYMENT_QUICKSTART.md
- [ ] I have bookmarked DEPLOYMENT_BTP.md
- [ ] I know where to check logs: `cf logs trexima-web --recent`
- [ ] I know where to get help:
  - GitHub Issues: https://github.com/miscarriage87/TREXIMA_Refactor/issues
  - SAP Community: https://community.sap.com/

---

## 📋 Quick Reference Commands

```bash
# Login
cf login -a https://api.cf.eu10.hana.ondemand.com

# Check target
cf target

# Deploy
cf push trexima-web

# Check status
cf app trexima-web

# View logs
cf logs trexima-web --recent

# Set environment variable
cf set-env trexima-web ODATA_URL "your-url"
cf restage trexima-web

# Scale application
cf scale trexima-web -m 1G

# Restart
cf restart trexima-web

# Delete (if needed)
cf delete trexima-web
```

---

## ✅ Ready to Deploy?

If you've checked all the items above, you're ready to deploy!

### Option 1: Automated Script
```bash
cd "/Users/cpohl/Documents/00 PRIVATE/00 Coding/CLAUDE CODE/TREXIMA"
./deploy.sh
```

### Option 2: Manual Steps
Follow DEPLOYMENT_QUICKSTART.md step by step

### Option 3: MTA Deployment
Follow DEPLOYMENT_BTP.md → Method 2

---

## 🆘 Something Not Ready?

### Missing SAP BTP Access?
- Request access from your BTP administrator
- Or sign up for free trial: https://www.sap.com/products/technology-platform/trial.html

### Missing CF CLI?
- See installation instructions in DEPLOYMENT_QUICKSTART.md

### Missing Dependencies?
- Run: `pip install -r requirements_new.txt`
- Verify: `python -c "import flask; import openpyxl; print('OK')"`

### Quota Issues?
- Contact your BTP administrator
- Or reduce memory in `manifest.yml`: `memory: 256M`

---

## 📊 Estimated Timeline

| Step | Duration | Task |
|------|----------|------|
| **Prerequisites** | 15 min | Install CF CLI, verify access |
| **Login** | 2 min | `cf login` |
| **Deploy** | 5 min | `cf push trexima-web` |
| **Configure** | 5 min | Set SF credentials |
| **Test** | 5 min | Verify functionality |
| **Total** | ~30 min | First-time deployment |

**Subsequent deployments:** ~5 minutes

---

## 🎯 Success Criteria

Your deployment is successful when:

✅ `cf app trexima-web` shows `state: running`
✅ Application URL is accessible in browser
✅ Home page displays correctly
✅ Export functionality works (can upload XML)
✅ Import functionality works (can upload Excel)
✅ No errors in logs: `cf logs trexima-web --recent`

---

**Ready to proceed? Follow DEPLOYMENT_QUICKSTART.md or run `./deploy.sh`**
