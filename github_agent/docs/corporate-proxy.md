# 🔧 Corporate Proxy Setup Guide

**Problem**: npm, git, and Prisma fail to download due to corporate proxy/SSL issues.

**Solution**: This comprehensive guide for Windows corporate environments.

---

## 🚀 Quick Fix (5 Minutes)

### Option 1: Automated Setup (Recommended)

```powershell
# Run the automated configuration script
.\setup-corporate-proxy.ps1
```

This will:
- ✅ Auto-detect your proxy settings
- ✅ Configure npm, git, and environment variables
- ✅ Create helper scripts for Prisma
- ✅ Handle SSL certificates

### Option 2: Manual Quick Fix

```powershell
# Set environment variables for current session
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
$env:PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING = "1"

# Now run Prisma
npm run db:generate
```

---

## 📋 Step-by-Step Manual Configuration

### Step 1: Find Your Proxy Settings

**Method A: Windows Settings**
```powershell
# PowerShell command to check proxy
Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
```

**Method B: Browser Settings**
- Chrome: Settings → System → Open proxy settings
- Edge: Settings → System → Open proxy settings
- Look for: `proxy.company.com:8080` or similar

**Method C: Ask IT**
- Request proxy server and port
- Request root SSL certificate (usually `.pem` or `.crt` file)

### Step 2: Configure npm

```powershell
# Set proxy
npm config set proxy http://proxy.company.com:8080
npm config set https-proxy http://proxy.company.com:8080

# Disable SSL verification (if corporate proxy breaks SSL)
npm config set strict-ssl false

# Use HTTP registry instead of HTTPS
npm config set registry http://registry.npmjs.org/

# If you have corporate certificate
npm config set cafile C:\certs\corp-root.pem
```

**Verify:**
```powershell
npm config list
```

### Step 3: Configure Git

```powershell
# Set proxy
git config --global http.proxy http://proxy.company.com:8080
git config --global https.proxy http://proxy.company.com:8080

# Disable SSL verification
git config --global http.sslVerify false
```

**Verify:**
```powershell
git config --global --list
```

### Step 4: Configure Environment Variables

**Temporary (current session only):**
```powershell
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
$env:PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING = "1"
```

**Permanent (requires admin):**
```powershell
# Run PowerShell as Administrator
[System.Environment]::SetEnvironmentVariable('HTTP_PROXY', 'http://proxy.company.com:8080', 'User')
[System.Environment]::SetEnvironmentVariable('HTTPS_PROXY', 'http://proxy.company.com:8080', 'User')
[System.Environment]::SetEnvironmentVariable('NODE_TLS_REJECT_UNAUTHORIZED', '0', 'User')

# Restart terminal after this
```

### Step 5: Handle SSL Certificates

**If you have corporate certificate:**
```powershell
# Set certificate path
$env:NODE_EXTRA_CA_CERTS = "C:\certs\corp-root.pem"

# Add to npm
npm config set cafile C:\certs\corp-root.pem

# Make permanent
[System.Environment]::SetEnvironmentVariable('NODE_EXTRA_CA_CERTS', 'C:\certs\corp-root.pem', 'User')
```

**If you DON'T have certificate (less secure):**
```powershell
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
```

---

## 🔧 Prisma-Specific Solutions

### Solution 1: Use Helper Script (Easiest)

After running `setup-corporate-proxy.ps1`, use:

```powershell
# Instead of: npm run db:generate
prisma-proxy.bat generate

# Instead of: npm run db:migrate
prisma-proxy.bat migrate

# Instead of: npx prisma studio
prisma-proxy.bat studio
```

### Solution 2: Direct Command with Environment Variables

```powershell
# PowerShell
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
npm run db:generate
```

### Solution 3: Modify package.json Scripts

Update `package.json`:
```json
{
  "scripts": {
    "db:generate": "cross-env NODE_TLS_REJECT_UNAUTHORIZED=0 HTTP_PROXY=http://proxy.company.com:8080 HTTPS_PROXY=http://proxy.company.com:8080 prisma generate",
    "db:migrate": "cross-env NODE_TLS_REJECT_UNAUTHORIZED=0 HTTP_PROXY=http://proxy.company.com:8080 HTTPS_PROXY=http://proxy.company.com:8080 prisma migrate dev"
  }
}
```

Install cross-env:
```powershell
npm install --save-dev cross-env
```

### Solution 4: Manual Engine Download

If automatic download fails:

```powershell
# Run manual download script
.\prisma-download-manual.ps1
```

Or download manually:
1. Go to: https://binaries.prisma.sh/
2. Find your Prisma version's commit hash
3. Download `schema-engine.exe.gz` and other engines
4. Extract to: `%USERPROFILE%\.cache\prisma\binaries\engines\{commit-hash}\windows\`

---

## 🆘 Common Errors & Fixes

### Error 1: "unable to get local issuer certificate"

**Cause**: Corporate proxy intercepts SSL connections

**Fix**:
```powershell
# Option A: Disable SSL verification
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"

# Option B: Use corporate certificate
$env:NODE_EXTRA_CA_CERTS = "C:\certs\corp-root.pem"
npm config set cafile C:\certs\corp-root.pem
```

### Error 2: "request to https://binaries.prisma.sh failed"

**Cause**: Prisma can't reach download server through proxy

**Fix**:
```powershell
# Set proxy environment variables
$env:HTTP_PROXY = "http://proxy.company.com:8080"
$env:HTTPS_PROXY = "http://proxy.company.com:8080"

# Skip checksum validation
$env:PRISMA_ENGINES_CHECKSUM_IGNORE_MISSING = "1"

# Try again
npm run db:generate
```

### Error 3: "Ignoring extra certs from C:\certs\corp-root.pem, load failed"

**Cause**: Certificate file format issue

**Fix**:
```powershell
# Temporarily disable certificate
$env:NODE_EXTRA_CA_CERTS = ""

# Use SSL bypass instead
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"

# Contact IT for correct certificate format (should be PEM)
```

### Error 4: npm install fails with ETIMEDOUT

**Cause**: Proxy timeout or authentication required

**Fix**:
```powershell
# Increase timeout
npm config set fetch-timeout 300000
npm config set fetch-retry-mintimeout 20000

# If proxy requires authentication
npm config set proxy http://username:password@proxy.company.com:8080
npm config set https-proxy http://username:password@proxy.company.com:8080
```

### Error 5: Prisma works but Docker doesn't

**Cause**: Docker needs separate proxy configuration

**Fix**:
```json
// %USERPROFILE%\.docker\config.json
{
  "proxies": {
    "default": {
      "httpProxy": "http://proxy.company.com:8080",
      "httpsProxy": "http://proxy.company.com:8080",
      "noProxy": "localhost,127.0.0.1"
    }
  }
}
```

---

## 🧪 Testing Your Configuration

### Test 1: npm
```powershell
npm install axios --save-dev
# Should download without errors
npm uninstall axios
```

### Test 2: Git
```powershell
git clone https://github.com/octocat/Hello-World.git test-repo
# Should clone successfully
Remove-Item -Recurse -Force test-repo
```

### Test 3: Prisma
```powershell
npm run db:generate
# Should download engines and generate client
```

### Test 4: Environment Variables
```powershell
# Check all variables are set
echo $env:HTTP_PROXY
echo $env:HTTPS_PROXY
echo $env:NODE_TLS_REJECT_UNAUTHORIZED
```

---

## 📝 Checklist

Use this checklist to ensure everything is configured:

- [ ] Proxy server and port identified
- [ ] npm proxy configured (`npm config list`)
- [ ] git proxy configured (`git config --global --list`)
- [ ] Environment variables set (HTTP_PROXY, HTTPS_PROXY)
- [ ] SSL handling configured (certificate or bypass)
- [ ] Prisma-specific env vars set (NODE_TLS_REJECT_UNAUTHORIZED)
- [ ] Helper scripts created (prisma-proxy.bat, npm-proxy.bat)
- [ ] npm install works
- [ ] Prisma generate works
- [ ] Docker proxy configured (if using Docker)

---

## 🔒 Security Considerations

**Warning**: Disabling SSL verification (`NODE_TLS_REJECT_UNAUTHORIZED=0`, `strict-ssl=false`) reduces security.

**Best Practice**:
1. Get proper corporate root certificate from IT
2. Use certificate instead of disabling verification
3. Only disable SSL for development, not production
4. Don't commit proxy passwords to git

**Safe Configuration**:
```powershell
# Use certificate (secure)
$env:NODE_EXTRA_CA_CERTS = "C:\certs\corp-root.pem"
npm config set cafile C:\certs\corp-root.pem
npm config set strict-ssl true

# Don't store passwords in config
# Use Windows Credential Manager instead
```

---

## 🆘 Still Having Issues?

### Information to Gather for IT Support

1. **Proxy details**:
   ```powershell
   Get-ItemProperty -Path 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Internet Settings'
   ```

2. **Network test**:
   ```powershell
   Test-NetConnection proxy.company.com -Port 8080
   ```

3. **npm config**:
   ```powershell
   npm config list
   ```

4. **Full error log**:
   ```powershell
   npm run db:generate --verbose > error.log 2>&1
   ```

### Ask IT For:

- ✅ Proxy server hostname and port
- ✅ Whether proxy requires authentication
- ✅ Corporate root SSL certificate (PEM format)
- ✅ Whitelist for: binaries.prisma.sh, registry.npmjs.org, github.com
- ✅ Docker registry access (if using Docker)

---

## 📚 Additional Resources

- [npm proxy configuration docs](https://docs.npmjs.com/cli/v9/using-npm/config#proxy)
- [Prisma proxy issues](https://github.com/prisma/prisma/issues?q=proxy)
- [Git proxy setup](https://git-scm.com/docs/git-config#Documentation/git-config.txt-httpproxy)

---

## ✅ Success!

Once configured, you should be able to:
```powershell
npm install          # Install packages
npm run db:generate  # Generate Prisma client
npm run db:migrate   # Run migrations
npm run dev          # Start development server
```

**All commands should work without proxy/SSL errors!** 🎉
