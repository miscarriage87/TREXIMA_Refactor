# TREXIMA v4.0 - Role Configuration Guide

**Date:** 2026-01-08
**Application:** https://trexima-v4.cfapps.eu10-004.hana.ondemand.com
**Subaccount:** hrisbtpsubaccount-yzr6xc10

---

## 🎯 Overview

TREXIMA requires two role collections to be set up for user access:

1. **TREXIMA_User** - Standard users who can create and manage translation projects
2. **TREXIMA_Admin** - Administrators with full access to all features

**Application ID:** `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248`

---

## ✅ Step-by-Step Setup (SAP BTP Cockpit)

### Step 1: Access SAP BTP Cockpit

1. Open your browser and go to: **https://cockpit.eu10.hana.ondemand.com**
2. Login with your SAP BTP credentials
3. Navigate to your subaccount: **hrisbtpsubaccount-yzr6xc10**

### Step 2: Navigate to Role Collections

1. In the left sidebar, click **Security**
2. Click **Role Collections**
3. You should see a list of existing role collections

### Step 3: Create "TREXIMA_User" Role Collection

1. Click the **"+"** button (or **"Create"**) at the top
2. Enter the following details:
   - **Name:** `TREXIMA_User`
   - **Description:** `Standard users for TREXIMA translation management`
3. Click **Create**

### Step 4: Add Roles to "TREXIMA_User" Collection

1. Click on the newly created **TREXIMA_User** role collection
2. Click the **Edit** button
3. Scroll down to the **Roles** section
4. Click **Add Role**
5. In the dialog, fill in:
   - **Application Identifier:** `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248`
   - **Role Template:** `User`
   - **Role:** `User`
6. Click **Add**
7. Click **Save** at the bottom

### Step 5: Create "TREXIMA_Admin" Role Collection

1. Go back to **Security** → **Role Collections**
2. Click the **"+"** button again
3. Enter:
   - **Name:** `TREXIMA_Admin`
   - **Description:** `Administrators for TREXIMA with full permissions`
4. Click **Create**

### Step 6: Add Roles to "TREXIMA_Admin" Collection

1. Click on the **TREXIMA_Admin** role collection
2. Click **Edit**
3. Scroll to **Roles** section and click **Add Role**
4. Add the **User** role first:
   - **Application Identifier:** `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248`
   - **Role Template:** `User`
   - **Role:** `User`
5. Click **Add**
6. Click **Add Role** again to add the **Admin** role:
   - **Application Identifier:** `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248`
   - **Role Template:** `Admin`
   - **Role:** `Admin`
7. Click **Add**
8. Click **Save**

### Step 7: Assign Users to Role Collections

#### For Standard Users:

1. Click on the **TREXIMA_User** role collection
2. Click **Edit**
3. Scroll to the **Users** section
4. Click **Add Users**
5. Enter user details:
   - **User:** Enter the user's email (e.g., `user@deloitte.de`)
   - **Identity Provider:** Select `Default identity provider` (or your custom IDP)
6. Click **Add**
7. Repeat for all standard users
8. Click **Save**

#### For Administrators:

1. Click on the **TREXIMA_Admin** role collection
2. Click **Edit**
3. Scroll to **Users** section
4. Click **Add Users**
5. Enter admin user details:
   - **User:** Enter the admin's email (e.g., `admin@deloitte.de`)
   - **Identity Provider:** Select `Default identity provider`
6. Click **Add**
7. Repeat for all administrators
8. Click **Save**

---

## 🔍 Verification

After setup, verify that roles are working:

1. **Check Role Collections:**
   - Go to **Security** → **Role Collections**
   - You should see:
     - ✅ `TREXIMA_User` (with User role)
     - ✅ `TREXIMA_Admin` (with User + Admin roles)

2. **Check User Assignments:**
   - Click on each role collection
   - Verify users are listed in the **Users** section

3. **Test Access:**
   - Have a user navigate to: https://trexima-v4.cfapps.eu10-004.hana.ondemand.com
   - They should be redirected to SAP authentication
   - After login, they should have access based on their role

---

## 👥 Role Permissions

### TREXIMA_User Role
Standard users can:
- ✅ Create new translation projects
- ✅ Upload XML data models
- ✅ Configure SuccessFactors connections
- ✅ Set export configuration (locales, objects)
- ✅ Generate translation workbooks
- ✅ Import translated workbooks
- ✅ Download generated files
- ✅ View their own projects

### TREXIMA_Admin Role
Administrators have all user permissions plus:
- ✅ View all projects (all users)
- ✅ Delete any project
- ✅ Access admin dashboard
- ✅ View system statistics
- ✅ Manage application settings (future)

---

## 🚨 Troubleshooting

### Issue: "Authorization error" when accessing the app

**Solution:**
1. Verify the user is assigned to a role collection
2. Check that the role collection contains the correct roles
3. Have the user logout and login again
4. Clear browser cache/cookies

### Issue: User can't see certain features

**Solution:**
1. Check if user has the correct role collection (User vs Admin)
2. Admin features require `TREXIMA_Admin` role collection
3. Verify role collection has both User and Admin roles assigned

### Issue: Role collections not visible

**Solution:**
1. Ensure you're in the correct subaccount
2. Check you have administrator permissions in SAP BTP Cockpit
3. Wait a few minutes - changes may take time to propagate

### Issue: Users can't login

**Solution:**
1. Verify XSUAA service is bound to the application
2. Check that users exist in the configured identity provider
3. Verify the application URL is accessible
4. Check application logs: `cf logs trexima-v4 --recent`

---

## 📝 Quick Reference

**Application URL:** https://trexima-v4.cfapps.eu10-004.hana.ondemand.com
**App ID:** na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248
**Cockpit URL:** https://cockpit.eu10.hana.ondemand.com
**Subaccount:** hrisbtpsubaccount-yzr6xc10

**CF Commands:**
```bash
# Check application status
cf app trexima-v4

# View recent logs
cf logs trexima-v4 --recent

# Check bound services
cf services

# View XSUAA service
cf service trexima-auth
```

---

## ✨ Next Steps After Role Setup

1. ✅ Users assigned to role collections
2. 🎯 Test application access with different user roles
3. 📊 Monitor application usage and logs
4. 🔄 Set up automated backups for PostgreSQL
5. 📚 Provide user training/documentation

---

**Setup Date:** 2026-01-08
**Version:** TREXIMA v4.0
**Status:** Production Ready
