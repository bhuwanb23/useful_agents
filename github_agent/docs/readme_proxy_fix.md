# 🚨 IMMEDIATE FIX for Prisma Download Error

You're seeing this error:
```
Error: request to https://binaries.prisma.sh failed
unable to get local issuer certificate
```

This is a **corporate proxy issue**. Here's the 2-minute fix:

---

## ⚡ Super Quick Fix (Copy-Paste This)

### Option 1: PowerShell (Recommended)

```powershell
# 1. Set these environment variables (update proxy URL first!)
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
$env:PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING = "1"

# 2. Configure npm
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080
npm config set strict-ssl false

# 3. Try Prisma again
npm run db:generate
```

### Option 2: Use Batch Script (Even Easier)

```cmd
REM 1. Edit quick-proxy-fix.bat and update PROXY_HOST and PROXY_PORT
REM 2. Run it:
quick-proxy-fix.bat

REM 3. Try Prisma again:
npm run db:generate
```

### Option 3: Automated Setup (Best)

```powershell
# Run the full setup script (it auto-detects your proxy):
.\setup-corporate-proxy.ps1

# Then use helper script:
prisma-proxy.bat generate
```

---

## 🔧 What You Need to Know

### 1. Find Your Proxy

**Don't know your proxy?** Run this:
```powershell
Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings' | Select-Object ProxyServer
```

It will show something like: `proxy.company.com:8080`

### 2. Update the Scripts

In **ALL scripts** (`quick-proxy-fix.bat`, `setup-corporate-proxy.ps1`), change:
```
proxy.company.com:8080
```
to YOUR actual proxy (from step 1).

### 3. Run the Fix

Pick ONE method above and run it.

---

## 🎯 After Running the Fix

Try these commands:
```powershell
# Test npm
npm install

# Test Prisma (this should now work!)
npm run db:generate

# Test migrations
npm run db:migrate

# Start the app
npm run dev
```

---

## 🆘 Still Not Working?

### Issue: Certificate Error Persists

**Solution**: You need the corporate root certificate.

1. Ask IT for the certificate file (usually `corp-root.pem` or `corp-root.crt`)
2. Save it to `C:\certs\corp-root.pem`
3. Run:
```powershell
$env:NODE_EXTRA_CA_CERTS = "C:\certs\corp-root.pem"
npm config set cafile C:\certs\corp-root.pem
npm run db:generate
```

### Issue: Proxy Requires Username/Password

**Solution**: Add credentials to proxy URL.

```powershell
$env:HTTP_PROXY = "http://YOUR_USERNAME:YOUR_PASSWORD@proxy.company.com:8080"
$env:HTTPS_PROXY = "http://YOUR_USERNAME:YOUR_PASSWORD@proxy.company.com:8080"

npm config set proxy http://YOUR_USERNAME:YOUR_PASSWORD@proxy.company.com:8080
npm config set https-proxy http://YOUR_USERNAME:YOUR_PASSWORD@proxy.company.com:8080
```

⚠️ **Warning**: Don't commit passwords to git!

---

## 📝 Quick Command Reference

| Task | Command |
|------|---------|
| Generate Prisma | `prisma-proxy.bat generate` |
| Run migrations | `prisma-proxy.bat migrate` |
| Install packages | `npm-proxy.bat install` |
| Prisma Studio | `prisma-proxy.bat studio` |
| Check config | `npm config list` |
| Reset npm config | `npm config delete proxy && npm config delete https-proxy` |

---

## ✅ Verification Checklist

Run these to verify everything is configured:

```powershell
# Check environment variables
echo $env:HTTP_PROXY        # Should show: http://proxy.company.com:8080
echo $env:HTTPS_PROXY       # Should show: http://proxy.company.com:8080
echo $env:NODE_TLS_REJECT_UNAUTHORIZED  # Should show: 0

# Check npm config
npm config get proxy        # Should show: http://proxy.company.com:8080
npm config get https-proxy  # Should show: http://proxy.company.com:8080
npm config get strict-ssl   # Should show: false

# Test npm
npm install axios --save-dev   # Should work
npm uninstall axios            # Clean up

# Test Prisma
npm run db:generate            # Should work now!
```

---

## 🎉 Success Looks Like This

```
> prisma generate

✔ Generated Prisma Client (5.x.x) to .\node_modules\@prisma\client in 150ms

✨ Prisma Client generated successfully!
```

No more errors! 🚀

---

## 📚 Need More Help?

- Read the full guide: `CORPORATE-PROXY-GUIDE.md`
- Check helper scripts: `prisma-proxy.bat`, `npm-proxy.bat`
- Run automated setup: `setup-corporate-proxy.ps1`

---

## 🔑 TL;DR - Just Run This

```powershell
# Copy-paste this entire block (update proxy URL first!)

$PROXY = "http://proxy.company.com:8080"  # ← UPDATE THIS!

$env:HTTP_PROXY = $PROXY
$env:HTTPS_PROXY = $PROXY
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
$env:PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING = "1"

npm config set proxy $PROXY
npm config set https-proxy $PROXY
npm config set strict-ssl false

Write-Host "✅ Proxy configured! Now run: npm run db:generate" -ForegroundColor Green
```

**That's it!** 🎯
