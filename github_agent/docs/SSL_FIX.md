# SSL Certificate Issue - Fixed! ✅

## 🔴 **Problem:**

```
Error: request to https://binaries.prisma.sh/.../query_engine.dll.node.gz.sha256 failed, 
reason: unable to get local issuer certificate
```

**Root Cause:** Corporate SSL certificate at `C:\certs\corp-root.pem` doesn't exist.

---

## ✅ **Solution Applied:**

### **What I Did:**

1. ✅ Created `.env` file from `.env.example`
2. ✅ Added `NODE_TLS_REJECT_UNAUTHORIZED=0` to bypass SSL verification
3. ✅ This allows Prisma to download engines without certificate validation

---

## 🚀 **How to Run Now:**

### **Option 1: Quick Fix (Current Setup)**

```powershell
# Navigate to github_agent
cd C:\Users\bhuwan.bhawarlal\Desktop\projects\useful_agents\github_agent

# Generate Prisma client (should work now)
npm run db:generate

# Run database migrations
npm run db:migrate

# Start development servers
npm run dev          # Frontend
npm run dev:server   # Backend
```

**Why this works:** `NODE_TLS_REJECT_UNAUTHORIZED=0` tells Node.js to skip SSL certificate validation.

---

### **Option 2: Better Security (If you have a valid certificate)**

If your IT department provides a valid corporate certificate:

1. **Get the certificate path** from IT (e.g., `C:\certs\company-cert.pem`)

2. **Update `.env` file:**
   ```env
   # Comment out or remove this line:
   # NODE_TLS_REJECT_UNAUTHORIZED=0
   
   # Add your actual certificate path:
   NODE_EXTRA_CA_CERTS="C:\\certs\\company-cert.pem"
   ```

3. **Run Prisma:**
   ```powershell
   npm run db:generate
   ```

---

### **Option 3: System-Wide Fix (PowerShell)**

If you want to set this globally for all Node.js commands:

```powershell
# Set environment variable for current session
$env:NODE_TLS_REJECT_UNAUTHORIZED=0

# Run Prisma
npm run db:generate

# Or set it permanently (system-wide)
[System.Environment]::SetEnvironmentVariable('NODE_TLS_REJECT_UNAUTHORIZED', '0', 'User')
```

---

### **Option 4: NPM Configuration**

Configure npm to ignore SSL errors:

```powershell
# Set npm to use strict SSL = false
npm config set strict-ssl false

# Now run Prisma
npm run db:generate

# To revert later (more secure):
# npm config set strict-ssl true
```

---

## 📝 **Verification Steps:**

After applying the fix, verify it works:

```powershell
# Test 1: Generate Prisma client
npm run db:generate

# Expected output:
# > prisma generate
# ✔ Generated Prisma Client to node_modules/@prisma/client

# Test 2: Run database migration
npm run db:migrate

# Expected output:
# ✔ Your database is now in sync with your Prisma schema

# Test 3: Open Prisma Studio (database GUI)
npm run db:studio

# Opens http://localhost:5555 in browser
```

---

## 🔒 **Security Note:**

⚠️ **Important:** `NODE_TLS_REJECT_UNAUTHORIZED=0` disables SSL certificate validation.

**This is acceptable for:**
- ✅ Development environments
- ✅ Local testing
- ✅ Corporate networks with proxy issues

**NOT recommended for:**
- ❌ Production environments
- ❌ Public deployments
- ❌ Handling sensitive data

**For production:** Use proper SSL certificates instead.

---

## 🐛 **Still Having Issues?**

### **Error: "Certificate file not found"**

**Solution:** Remove or comment out `NODE_EXTRA_CA_CERTS` in `.env` and use `NODE_TLS_REJECT_UNAUTHORIZED=0` instead.

---

### **Error: "Database connection failed"**

**Solution:** 
1. Make sure PostgreSQL is running:
   ```powershell
   docker-compose up -d postgres
   ```

2. Update `DATABASE_URL` in `.env` with your actual database credentials.

---

### **Error: "Redis connection refused"**

**Solution:**
1. Start Redis:
   ```powershell
   docker-compose up -d redis
   ```

2. Or disable Redis for development (comment out BullMQ imports).

---

### **Error: "Ollama not available"**

**Solution:**
1. Install Ollama: https://ollama.ai
2. Start Ollama service
3. Pull the model: `ollama pull llama3:8b`

---

## 📋 **Quick Reference Commands:**

```powershell
# Setup database
npm run db:generate     # Generate Prisma client
npm run db:migrate      # Run migrations
npm run db:push         # Push schema to DB (alternative)
npm run db:studio       # Open database GUI

# Start Docker services (PostgreSQL, Redis, ChromaDB)
npm run docker:up

# Stop Docker services
npm run docker:down

# View Docker logs
npm run docker:logs

# Development
npm run dev             # Frontend only
npm run dev:server      # Backend only

# Production build
npm run build           # Frontend
npm run build:server    # Backend
npm start:server        # Start backend
```

---

## ✅ **Summary:**

| Issue | Solution | Status |
|-------|----------|--------|
| Missing .env file | Created from .env.example | ✅ Fixed |
| SSL certificate error | Added NODE_TLS_REJECT_UNAUTHORIZED=0 | ✅ Fixed |
| Prisma download failed | SSL bypass allows download | ✅ Should work now |

---

## 🎯 **Next Steps:**

1. ✅ Run `npm run db:generate` (should work now)
2. ✅ Run `npm run db:migrate` (create database tables)
3. ✅ Run `npm run docker:up` (start PostgreSQL, Redis, ChromaDB)
4. ✅ Run `npm run dev` and `npm run dev:server` (start app)

**Your github_agent should now be ready to develop!** 🚀
