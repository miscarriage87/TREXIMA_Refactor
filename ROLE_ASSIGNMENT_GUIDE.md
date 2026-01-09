# TREXIMA v4.0 - Role Assignment Guide (Updated)

**Date:** 2026-01-09
**Application:** https://trexima-v4.cfapps.eu10-004.hana.ondemand.com
**Status:** ✅ Roles Configured Successfully

---

## ✅ **What's Already Done**

The XSUAA service has been updated with the proper role configuration. Two role collections are now available:

1. **TREXIMA_Admin** - Administrators with full access
2. **TREXIMA_User** - Standard users

**Application ID:** `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248`

---

## 🎯 **How to Assign Users (SAP BTP Cockpit)**

### Step 1: Access Role Collections

1. Open SAP BTP Cockpit: **https://cockpit.eu10.hana.ondemand.com**
2. Navigate to your subaccount: **hrisbtpsubaccount-yzr6xc10**
3. Click **Security** → **Role Collections** in the left sidebar

### Step 2: Find TREXIMA Role Collections

You should now see these role collections in the list:
- ✅ **TREXIMA_Admin**
- ✅ **TREXIMA_User**

### Step 3: Assign Users to TREXIMA_User Role

1. Click on **TREXIMA_User** from the list
2. You'll see the role collection details with:
   - Description: "TREXIMA User Role Collection"
   - One role assigned: `User` from application `na-ac7cefd4...!t383248`
3. Click the **Edit** button (top right)
4. Scroll down to the **Users** section
5. Click **Add Users** (or the + button)
6. Enter user details:
   - **User Name/Email:** `user@deloitte.de` (replace with actual email)
   - **Identity Provider:** Select `Default identity provider` (or your custom IDP)
7. Click **Add**
8. Repeat steps 5-7 for all standard users
9. Click **Save** at the bottom

### Step 4: Assign Administrators to TREXIMA_Admin Role

1. Go back to **Security** → **Role Collections**
2. Click on **TREXIMA_Admin** from the list
3. You'll see:
   - Description: "TREXIMA Administrator Role Collection"
   - Two roles assigned: `User` and `Admin`
4. Click **Edit**
5. Scroll to the **Users** section
6. Click **Add Users**
7. Enter admin details:
   - **User Name/Email:** `cpohl@deloitte.de` (your admin email)
   - **Identity Provider:** `Default identity provider`
8. Click **Add**
9. Repeat for all administrator users
10. Click **Save**

---

## 🔍 **Verification Steps**

### 1. Check Role Collection Contents

**TREXIMA_User should have:**
- ✅ 1 role: `User` template
- ✅ Scope: `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248.user`

**TREXIMA_Admin should have:**
- ✅ 2 roles: `User` and `Admin` templates
- ✅ Scopes:
  - `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248.user`
  - `na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f!t383248.admin`

### 2. Test User Access

1. Have an assigned user navigate to: **https://trexima-v4.cfapps.eu10-004.hana.ondemand.com**
2. User should be redirected to SAP login page
3. After successful login, user should see the TREXIMA application
4. User can create projects and access standard features

### 3. Test Admin Access

1. Admin navigates to: **https://trexima-v4.cfapps.eu10-004.hana.ondemand.com**
2. After login, admin should see all features including:
   - All projects (not just their own)
   - Admin dashboard (when implemented)
   - Full permissions

---

## 👥 **Role Permissions Breakdown**

### TREXIMA_User (Standard Access)
Users with this role collection can:
- ✅ Login to TREXIMA application
- ✅ Create new translation projects
- ✅ Upload XML data models
- ✅ Configure SuccessFactors connections
- ✅ Set export configuration (languages, objects)
- ✅ Generate translation workbooks
- ✅ Import translated workbooks
- ✅ Download generated files
- ✅ View and manage their own projects

### TREXIMA_Admin (Full Access)
Administrators have all user permissions PLUS:
- ✅ View all projects from all users
- ✅ Delete any project
- ✅ Access admin features
- ✅ View system statistics
- ✅ Manage application settings

---

## 🚨 **Troubleshooting**

### Issue: Role collections not visible

**Possible Causes:**
1. Service update not complete
2. Wrong subaccount
3. Insufficient permissions in BTP Cockpit

**Solution:**
```bash
# Check XSUAA service status
cf service trexima-auth

# Should show: status: update succeeded
```

If service shows "update in progress", wait a few minutes and refresh the Cockpit.

### Issue: Application shows "Authorization Required" error

**Solution:**
1. Verify user is assigned to a role collection
2. Have user **logout and login again**
3. Clear browser cache/cookies
4. Check application logs:
   ```bash
   cf logs trexima-v4 --recent
   ```

### Issue: User sees "Insufficient permissions" message

**Solution:**
1. Verify the correct role collection is assigned:
   - Standard features need `TREXIMA_User`
   - Admin features need `TREXIMA_Admin`
2. Check that the role collection contains the correct roles
3. Wait 5-10 minutes for changes to propagate
4. Have user logout and login again

### Issue: Role collections show but are empty (no roles)

**Solution:**
This means the XSUAA service update didn't complete properly.

1. Check service status:
   ```bash
   cf service trexima-auth
   ```

2. If needed, update service again:
   ```bash
   cd /Users/cpohl/Documents/00\ PRIVATE/00\ Coding/CLAUDE\ CODE/TREXIMA
   cf update-service trexima-auth -c xs-security.json
   ```

3. Restage application:
   ```bash
   cf restage trexima-v4
   ```

---

## 📋 **Quick Reference**

### Current Configuration
```json
{
  "xsappname": "na-ac7cefd4-d67a-413f-87b2-8b6c749baa0f",
  "role-collections": [
    {
      "name": "TREXIMA_Admin",
      "roles": ["User", "Admin"]
    },
    {
      "name": "TREXIMA_User",
      "roles": ["User"]
    }
  ]
}
```

### Useful Commands

**Check app status:**
```bash
cf app trexima-v4
```

**Check XSUAA service:**
```bash
cf service trexima-auth
```

**View app logs:**
```bash
cf logs trexima-v4 --recent
```

**Test health endpoint:**
```bash
curl https://trexima-v4.cfapps.eu10-004.hana.ondemand.com/api/health
```

**Restage app (if needed):**
```bash
cf restage trexima-v4
```

---

## 📞 **Support**

### Where to Get Help

1. **Application Issues:**
   - Check logs: `cf logs trexima-v4 --recent`
   - Test health: https://trexima-v4.cfapps.eu10-004.hana.ondemand.com/api/health

2. **Authorization Issues:**
   - Verify role assignments in BTP Cockpit
   - Check XSUAA service status
   - Review this guide's troubleshooting section

3. **BTP Cockpit Access:**
   - URL: https://cockpit.eu10.hana.ondemand.com
   - Subaccount: hrisbtpsubaccount-yzr6xc10
   - Section: Security → Role Collections

---

## ✅ **Success Criteria**

Your role setup is complete when:
- [ ] You can see **TREXIMA_User** in Role Collections
- [ ] You can see **TREXIMA_Admin** in Role Collections
- [ ] Each role collection contains the correct roles
- [ ] Users are assigned to role collections
- [ ] Users can successfully login to the application
- [ ] Users can access features based on their role

---

## 📝 **Example User Assignment**

### Standard Users (TREXIMA_User)
- user1@deloitte.de
- user2@deloitte.de
- translator1@deloitte.de
- translator2@deloitte.de

### Administrators (TREXIMA_Admin)
- cpohl@deloitte.de (you)
- admin@deloitte.de
- manager@deloitte.de

**Remember:** Users need to logout and login again after role assignment!

---

**Last Updated:** 2026-01-09
**XSUAA Service:** trexima-auth ✅ Updated
**Application:** trexima-v4 ✅ Running
**Status:** Ready for user assignment
