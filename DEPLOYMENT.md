# TREXIMA v4.0 - Deployment Guide

**Target Platform:** SAP Business Technology Platform (BTP) Cloud Foundry
**Status:** Production Ready
**Date:** 2026-01-08

---

## 🎯 Quick Start

### Prerequisites
1. **Cloud Foundry CLI** installed
   ```bash
   # macOS
   brew install cloudfoundry/tap/cf-cli@8

   # Or download from: https://github.com/cloudfoundry/cli/releases
   ```

2. **Node.js** (v18+) and **Python** (3.10+)
3. **SAP BTP Account** with Cloud Foundry environment
4. **Space** created in your Cloud Foundry organization

### Deployment Steps

```bash
# 1. Login to SAP BTP
cf login -a https://api.cf.eu10.hana.ondemand.com

# 2. Create required services
./create-services.sh

# 3. Deploy application
./deploy.sh
```

That's it! The application will be deployed and accessible at your configured route.

---

## 📋 Detailed Deployment Instructions

### Step 1: Prepare Your Environment

1. **Clone the repository** (if not already done)
   ```bash
   git clone <your-repo-url>
   cd TREXIMA
   ```

2. **Verify file structure**
   ```
   TREXIMA/
   ├── manifest.yml              ✓ Created
   ├── Procfile                  ✓ Created
   ├── runtime.txt               ✓ Created
   ├── .cfignore                 ✓ Created
   ├── requirements.txt          ✓ Exists
   ├── deploy.sh                 ✓ Created
   ├── create-services.sh        ✓ Created
   ├── .env.template             ✓ Created
   ├── trexima/                  ✓ Backend code
   └── trexima-frontend/         ✓ Frontend code
   ```

### Step 2: Configure Deployment

1. **Review `manifest.yml`**
   ```yaml
   applications:
   - name: trexima-v4
     memory: 1G
     disk_quota: 2G
     instances: 1
     routes:
       - route: trexima-v4.cfapps.eu10.hana.ondemand.com  # Update this!
   ```

2. **Update route** (optional)
   - Change `trexima-v4.cfapps.eu10.hana.ondemand.com` to your desired domain
   - Or use default and map custom domain later

3. **Configure environment** (optional)
   - Most settings are auto-configured from bound services
   - Override in `manifest.yml` `env:` section if needed

### Step 3: Create SAP BTP Services

Run the service creation script:

```bash
./create-services.sh
```

This creates:
1. **trexima-postgres** - PostgreSQL database (v9.6-small)
2. **trexima-objectstore** - S3-compatible object storage
3. **trexima-xsuaa** - XSUAA authentication service

**Service creation takes 2-5 minutes.** The script waits for all services to be ready.

### Step 4: Deploy Application

Run the deployment script:

```bash
./deploy.sh
```

The script will:
1. ✓ Check prerequisites (cf CLI, node, python)
2. ✓ Login to Cloud Foundry (prompts for credentials)
3. ✓ Build React frontend (`npm run build`)
4. ✓ Copy static assets to Flask app
5. ✓ Verify required services exist
6. ✓ Push application to Cloud Foundry
7. ✓ Run database migrations
8. ✓ Display deployment status and URL

**Deployment takes 3-5 minutes.**

### Step 5: Verify Deployment

1. **Check application status**
   ```bash
   cf app trexima-v4
   ```

2. **View logs**
   ```bash
   cf logs trexima-v4 --recent
   ```

3. **Test health endpoint**
   ```bash
   curl https://trexima-v4.cfapps.eu10.hana.ondemand.com/api/health
   ```

4. **Access application**
   - Open: `https://trexima-v4.cfapps.eu10.hana.ondemand.com`
   - Should see TREXIMA login page

---

## 🔧 Configuration Details

### Buildpacks

The application uses two buildpacks:
1. **python_buildpack** - For Flask backend
2. **nodejs_buildpack** - For frontend build process

Order matters! Python buildpack runs first.

### Environment Variables

**Auto-configured from VCAP_SERVICES:**
- `VCAP_SERVICES` - Service credentials (PostgreSQL, Object Store, XSUAA)
- `VCAP_APPLICATION` - Application metadata
- `PORT` - Dynamic port assignment

**Set in manifest.yml:**
- `FLASK_ENV=production` - Flask production mode
- `PYTHONUNBUFFERED=true` - Real-time log output
- `WEB_CONCURRENCY=4` - Gunicorn worker count
- `MAX_CONTENT_LENGTH=104857600` - 100MB max upload
- `APP_NAME`, `VERSION` - Application metadata
- `SESSION_TYPE=filesystem` - Session storage
- `CORS_ORIGINS` - CORS configuration

### Service Bindings

**PostgreSQL (trexima-postgres):**
- Provides: `DATABASE_URL`, `uri`, `hostname`, `port`, `username`, `password`
- Used for: Project data, user data, file metadata
- Auto-configured in `app.py` from `VCAP_SERVICES`

**Object Store (trexima-objectstore):**
- Provides: S3-compatible credentials
- Used for: File uploads (XML), generated workbooks, reports
- Auto-configured in `storage.py` from `VCAP_SERVICES`

**XSUAA (trexima-xsuaa):**
- Provides: OAuth2 endpoints, client credentials
- Used for: User authentication, role-based access
- Auto-configured in `auth.py` from `VCAP_SERVICES`

### Health Check

**Endpoint:** `/api/health`
**Type:** HTTP health check
**Timeout:** 180 seconds

Returns:
```json
{
  "status": "healthy",
  "version": "4.0.0",
  "timestamp": "2026-01-08T10:00:00Z"
}
```

---

## 🚀 Advanced Deployment

### Scaling

**Scale instances:**
```bash
cf scale trexima-v4 -i 2
```

**Scale memory:**
```bash
cf scale trexima-v4 -m 2G
```

**Scale disk:**
```bash
cf scale trexima-v4 -k 3G
```

### Blue-Green Deployment

```bash
# Deploy new version as trexima-v4-green
cf push trexima-v4-green -f manifest.yml

# Test green deployment
curl https://trexima-v4-green.cfapps.eu10.hana.ondemand.com/api/health

# Map route to green
cf map-route trexima-v4-green cfapps.eu10.hana.ondemand.com --hostname trexima-v4

# Unmap route from blue
cf unmap-route trexima-v4 cfapps.eu10.hana.ondemand.com --hostname trexima-v4

# Delete blue after verification
cf delete trexima-v4 -f

# Rename green to blue
cf rename trexima-v4-green trexima-v4
```

### Environment-Specific Deployments

**Development:**
```bash
cf push -f manifest.yml --var env=dev
```

**Production:**
```bash
cf push -f manifest.yml --var env=prod
```

### Database Migrations

**Manual migration:**
```bash
cf run-task trexima-v4 "python -c 'from trexima.web.app import create_app; from trexima.web.models import db; app = create_app(); app.app_context().push(); db.create_all()'" --name db-migration
```

**Check migration status:**
```bash
cf tasks trexima-v4
```

---

## 🔍 Monitoring & Maintenance

### View Logs

**Stream real-time logs:**
```bash
cf logs trexima-v4
```

**Recent logs:**
```bash
cf logs trexima-v4 --recent
```

**Filter logs:**
```bash
cf logs trexima-v4 | grep ERROR
```

### Application Status

**Full status:**
```bash
cf app trexima-v4
```

**Events:**
```bash
cf events trexima-v4
```

**Environment variables:**
```bash
cf env trexima-v4
```

### Restart/Restage

**Restart (quick):**
```bash
cf restart trexima-v4
```

**Restage (rebuild):**
```bash
cf restage trexima-v4
```

### Service Status

**Check all services:**
```bash
cf services
```

**Specific service:**
```bash
cf service trexima-postgres
```

**Service key (credentials):**
```bash
cf service-key trexima-postgres trexima-key
```

---

## 🛠️ Troubleshooting

### Application Won't Start

1. **Check logs:**
   ```bash
   cf logs trexima-v4 --recent
   ```

2. **Verify services:**
   ```bash
   cf services
   ```

3. **Check environment:**
   ```bash
   cf env trexima-v4
   ```

4. **Validate manifest:**
   ```bash
   cf push --dry-run -f manifest.yml
   ```

### Database Connection Issues

1. **Verify PostgreSQL service:**
   ```bash
   cf service trexima-postgres
   ```

2. **Check connection string:**
   ```bash
   cf env trexima-v4 | grep -A 20 VCAP_SERVICES
   ```

3. **Test connection:**
   ```bash
   cf run-task trexima-v4 "python -c 'from trexima.web.models import db; print(db.engine.url)'"
   ```

### Object Store Issues

1. **Verify service:**
   ```bash
   cf service trexima-objectstore
   ```

2. **Check credentials:**
   ```bash
   cf service-key trexima-objectstore show-key
   ```

3. **Test access:**
   - Upload test file via UI
   - Check logs for S3 errors

### Authentication Issues

1. **Verify XSUAA service:**
   ```bash
   cf service trexima-xsuaa
   ```

2. **Check role assignments:**
   - SAP BTP Cockpit → Security → Role Collections
   - Assign users to "TREXIMA User" or "TREXIMA Admin" roles

3. **Test auth flow:**
   - Access `/api/auth/login`
   - Should redirect to XSUAA login

### Performance Issues

1. **Check resource usage:**
   ```bash
   cf app trexima-v4
   ```

2. **Scale if needed:**
   ```bash
   cf scale trexima-v4 -m 2G -i 2
   ```

3. **Review slow queries:**
   - Check PostgreSQL logs
   - Add database indexes if needed

---

## 📦 Rollback Procedure

### Quick Rollback

```bash
# Stop current app
cf stop trexima-v4

# Deploy previous version
cf push trexima-v4-rollback -f manifest.yml

# Test
curl https://trexima-v4-rollback.cfapps.eu10.hana.ondemand.com/api/health

# Swap routes
cf map-route trexima-v4-rollback cfapps.eu10.hana.ondemand.com --hostname trexima-v4
cf unmap-route trexima-v4 cfapps.eu10.hana.ondemand.com --hostname trexima-v4

# Cleanup
cf delete trexima-v4 -f
cf rename trexima-v4-rollback trexima-v4
```

### Database Rollback

**Backup before migrations:**
```bash
# Create service key
cf create-service-key trexima-postgres backup-key

# Get credentials
cf service-key trexima-postgres backup-key

# Backup with pg_dump
pg_dump -h <host> -U <user> -d <database> > backup.sql
```

**Restore:**
```bash
psql -h <host> -U <user> -d <database> < backup.sql
```

---

## 🔐 Security Considerations

### XSUAA Configuration

- **Role-based access control** via XSUAA
- **OAuth2 authentication** flow
- **JWT tokens** for API access
- **User roles:** User (standard), Admin (elevated)

### Environment Variables

- **Never commit** `.env` files
- **Use VCAP_SERVICES** for credentials in production
- **Rotate secrets** regularly

### HTTPS

- **Always use HTTPS** in production
- Cloud Foundry provides SSL termination
- Custom domains: Configure SSL certificate in BTP

### CORS

- **Configure CORS_ORIGINS** in production
- Don't use `*` wildcard for production
- List specific allowed origins

---

## 📊 Production Checklist

Before going live, verify:

- [ ] All services created and bound
- [ ] Database migrations completed
- [ ] Health check endpoint responds
- [ ] User authentication works (XSUAA)
- [ ] File upload works (Object Store)
- [ ] Export workflow completes
- [ ] Import workflow completes
- [ ] WebSocket connections work
- [ ] Logs configured and accessible
- [ ] Monitoring set up
- [ ] Backup strategy defined
- [ ] Rollback procedure tested
- [ ] Security scan completed
- [ ] Load testing passed
- [ ] User documentation ready

---

## 🎯 Next Steps

After successful deployment:

1. **Configure Users**
   - Assign role collections in BTP Cockpit
   - Test user and admin access

2. **Set Up Monitoring**
   - Configure log forwarding (Splunk, ELK)
   - Set up alerts for errors
   - Monitor resource usage

3. **Performance Tuning**
   - Adjust worker count if needed
   - Scale instances based on load
   - Optimize database queries

4. **Backup Strategy**
   - Schedule database backups
   - Define retention policy
   - Test restore procedure

5. **Documentation**
   - User guide for end users
   - Admin guide for operations
   - API documentation

---

## 📞 Support

**Deployment Issues:**
- Check this document first
- Review application logs: `cf logs trexima-v4`
- Check service status: `cf services`

**Application Issues:**
- Access logs: `cf logs trexima-v4 --recent`
- Check health: `https://your-app-url/api/health`
- Review TESTING_REPORT.md for known issues

---

**Deployment Guide Version:** 1.0
**Last Updated:** 2026-01-08
**Status:** ✅ Production Ready
