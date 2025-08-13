# 🔐 Render Environment Variables

## Required Environment Variables for Authentication

Your Bottie API uses these environment variables on Render for authentication:

### **User Credentials**
```
SUPERUSER_PASSWORD=SuperSecret123!
ADMIN_PASSWORD=AdminPass456!
```

### **Default Values (if not set on Render)**
- **superuser**: `SuperSecret123!`
- **admin**: `AdminPass456!`

## 🚀 To Update Passwords on Render:

1. **Go to your Render dashboard**
2. **Select your Bottie service**
3. **Go to Environment tab**
4. **Add/Update these variables:**
   - `SUPERUSER_PASSWORD` → Your secure superuser password
   - `ADMIN_PASSWORD` → Your secure admin password

## 🎯 Current Login Credentials

### **For Netlify Frontend:**
- **Admin**: `admin` / `AdminPass456!`
- **Superuser**: `superuser` / `SuperSecret123!`

### **Security Recommendations:**

1. **Change default passwords** on Render:
   ```
   SUPERUSER_PASSWORD=YourSecurePassword123!
   ADMIN_PASSWORD=YourAdminPassword456!
   ```

2. **Restart your Render service** after updating environment variables

3. **Update your local frontend** if using custom passwords:
   - Edit `web/index_netlify.html` line ~211
   - Change the `value="AdminPass456!"` to your new password

## 🔍 **Why This Matters:**

- Your API reads passwords from Render environment variables
- The frontend needs to match these passwords
- Default passwords are used if environment variables aren't set
- This provides security while allowing easy deployment

## 🎉 **Next Steps:**

1. Upload corrected files to Netlify (`index.html` + `app.js`)
2. Test login with `admin` / `AdminPass456!`
3. Consider updating passwords on Render for better security
4. Update frontend defaults if you change Render passwords
