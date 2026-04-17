# 📦 Installation Guide - GitHub Agent System

Complete step-by-step installation guide for all environments.

---

## 🚨 Step 0: Corporate Proxy Setup (If Applicable)

**Are you behind a corporate firewall/proxy?**

If `npm install` or any downloads fail with SSL/certificate errors:

### Quick Fix
See **[START-HERE.md](./START-HERE.md)** for instant solutions.

### Tools Available
- `quick-proxy-fix.bat` - Windows one-click
- `node setup-proxy.js` - Auto-detection
- **[README-PROXY-FIX.md](./README-PROXY-FIX.md)** - 2-min guide
- **[CORPORATE-PROXY-GUIDE.md](./CORPORATE-PROXY-GUIDE.md)** - Complete guide

**Fix proxy issues first, then continue below.**

---

## 📋 Prerequisites

### Required Software

| Software | Version | Download |
|----------|---------|----------|
| **Node.js** | 18.x or higher | https://nodejs.org/ |
| **npm** | 9.x or higher | (comes with Node.js) |
| **Docker Desktop** | Latest | https://www.docker.com/products/docker-desktop/ |
| **Git** | Latest | https://git-scm.com/ |

### Optional but Recommended

| Software | Purpose |
|----------|---------|
| **VSCode** | Code editing |
| **PostgreSQL Client** | Database inspection |
| **Postman/Insomnia** | API testing |

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **OS**: Windows 10+, macOS 10.15+, or Linux

---

## 🚀 Installation Steps

### Step 1: Clone Repository

```bash
git clone <your-repo-url>
cd github_agent
```

### Step 2: Install Dependencies

```bash
npm install
```

**Troubleshooting:**
- If behind proxy: See [START-HERE.md](./START-HERE.md)
- If `EACCES` error: Don't use `sudo`, fix permissions instead
- If slow: Increase timeout: `npm config set fetch-timeout 300000`

### Step 3: Start Infrastructure

```bash
# Start all services (PostgreSQL, Redis, ChromaDB, Ollama)
docker-compose up -d

# Verify all containers are running
docker-compose ps
```

**Expected output:**
```
NAME                     STATUS    PORTS
github-agent-postgres    Up        5432
github-agent-redis       Up        6379
github-agent-chromadb    Up        8000
github-agent-ollama      Up        11434
```

**Troubleshooting:**
- If Docker not running: Start Docker Desktop
- If port conflicts: Check `docker-compose.yml`, change ports
- If memory errors: Increase Docker memory limit in Docker Desktop settings

### Step 4: Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

**Required variables:**
```env
# Database (already configured for Docker)
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/github_agent"

# Redis (already configured for Docker)
REDIS_URL="redis://localhost:6379"

# GitHub (create at: https://github.com/settings/tokens)
GITHUB_TOKEN="ghp_your_token_here"
GITHUB_WEBHOOK_SECRET="your_webhook_secret_here"

# Ollama
OLLAMA_BASE_URL="http://localhost:11434"

# ChromaDB
CHROMA_URL="http://localhost:8000"

# API Server
PORT=3001
NODE_ENV=development
```

**How to get GitHub token:**
1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Select scopes: `repo`, `workflow`, `admin:repo_hook`
4. Copy token and paste in `.env`

### Step 5: Setup Database

```bash
# Generate Prisma client
npm run db:generate

# Run migrations
npm run db:migrate

# Seed initial data (optional)
npm run db:seed
```

**If `db:generate` fails (corporate proxy):**
```bash
# Windows
prisma-proxy.bat generate

# Or set env vars first
$env:HTTP_PROXY = "http://proxy:8080"
$env:HTTPS_PROXY = "http://proxy:8080"
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
npm run db:generate
```

### Step 6: Download AI Model

```bash
# Pull the AI model (choose one)
docker exec github-agent-ollama-1 ollama pull llama3.2:3b    # Fast, 2GB
docker exec github-agent-ollama-1 ollama pull llama3:8b      # Balanced, 4.7GB
docker exec github-agent-ollama-1 ollama pull codellama:13b  # Best for code, 7GB

# Verify model is downloaded
docker exec github-agent-ollama-1 ollama list
```

**Model recommendations:**
- **Development/Testing**: llama3.2:3b (fastest)
- **Production**: llama3:8b (balanced)
- **Code-heavy tasks**: codellama:13b (best quality)

### Step 7: Start Backend Server

```bash
# Terminal 1: Start API server
npm run server

# Should see:
# ✅ Database connected
# ✅ Redis connected
# 🚀 Server running on http://localhost:3001
```

**Verify backend:**
```bash
curl http://localhost:3001/health
# Should return: {"status":"ok","database":"connected","redis":"connected"}
```

### Step 8: Start Task Workers

```bash
# Terminal 2: Start background workers
npm run worker

# Should see:
# ✅ Worker started
# ✅ Listening to queues: analyzer, fixer, reviewer, security, tester, docs, manager
```

### Step 9: Start Frontend

```bash
# Terminal 3: Start React dashboard
npm run dev

# Should see:
# ➜  Local:   http://localhost:5173/
```

**Open browser to: http://localhost:5173**

---

## ✅ Verification Checklist

Run through this checklist to ensure everything is working:

### Infrastructure
- [ ] Docker containers running: `docker-compose ps`
- [ ] PostgreSQL accessible: `docker exec -it github-agent-postgres-1 psql -U postgres`
- [ ] Redis accessible: `docker exec -it github-agent-redis-1 redis-cli ping`
- [ ] ChromaDB accessible: `curl http://localhost:8000/api/v1/heartbeat`
- [ ] Ollama accessible: `curl http://localhost:11434/api/tags`

### Database
- [ ] Prisma generated: `node_modules/.prisma/client` exists
- [ ] Migrations applied: `npx prisma studio` opens
- [ ] Tables created: Check in Prisma Studio

### Backend
- [ ] Server running: `curl http://localhost:3001/health`
- [ ] WebSocket working: Dashboard shows "Connected" status
- [ ] Workers running: Check terminal for "Worker started" message

### Frontend
- [ ] Dashboard loads: http://localhost:5173
- [ ] Navigation works: Click through all tabs
- [ ] Real-time updates: Check logs streaming

### AI/LLM
- [ ] Model downloaded: `docker exec github-agent-ollama-1 ollama list`
- [ ] Model responds: `curl http://localhost:11434/api/generate -d '{"model":"llama3:8b","prompt":"hello"}'`

### RAG System
- [ ] ChromaDB running: `curl http://localhost:8000/api/v1/heartbeat`
- [ ] Collections created: Check in dashboard

---

## 🧪 Test the System

### Test 1: Health Check

```bash
curl http://localhost:3001/health
```

**Expected:**
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "ollama": "connected",
  "chromadb": "connected"
}
```

### Test 2: Create a Repository

```bash
curl -X POST http://localhost:3001/api/repositories \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-repo",
    "owner": "your-username",
    "url": "https://github.com/your-username/test-repo",
    "autoPilot": false
  }'
```

### Test 3: Analyze an Issue

```bash
curl -X POST http://localhost:3001/api/issues/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "issueNumber": 1,
    "repositoryId": 1
  }'
```

### Test 4: Check Dashboard

1. Open: http://localhost:5173
2. Go to "Repositories" tab
3. See your test repo
4. Go to "Issues" tab
5. See analysis in progress

---

## 🔧 Common Issues & Solutions

### Issue: `npm install` fails with SSL error

**Solution:** You're behind a corporate proxy.
```bash
# Quick fix
node setup-proxy.js

# Or read: START-HERE.md
```

### Issue: Docker containers won't start

**Solution:**
```bash
# Check Docker is running
docker ps

# Restart Docker Desktop
# Then:
docker-compose down
docker-compose up -d
```

### Issue: Port already in use

**Solution:**
```bash
# Find what's using the port
# Windows PowerShell:
Get-Process -Id (Get-NetTCPConnection -LocalPort 3001).OwningProcess

# macOS/Linux:
lsof -i :3001

# Kill the process or change port in .env
```

### Issue: Prisma generate fails

**Solution:**
```bash
# Clear Prisma cache
rm -rf node_modules/.prisma
rm -rf node_modules/@prisma

# Reinstall
npm install

# Try with proxy settings
prisma-proxy.bat generate  # Windows
# OR
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
npm run db:generate
```

### Issue: Database migrations fail

**Solution:**
```bash
# Reset database
npx prisma migrate reset

# Or start fresh
docker-compose down -v
docker-compose up -d
npm run db:migrate
```

### Issue: Ollama model won't download

**Solution:**
```bash
# Check container is running
docker ps | grep ollama

# Check logs
docker logs github-agent-ollama-1

# Try downloading directly
docker exec -it github-agent-ollama-1 ollama pull llama3:8b

# If behind proxy, configure Docker proxy in:
# ~/.docker/config.json (see CORPORATE-PROXY-GUIDE.md)
```

### Issue: Frontend shows connection error

**Solution:**
```bash
# 1. Check backend is running
curl http://localhost:3001/health

# 2. Check WebSocket port in frontend
# src/config/api.ts should match backend port

# 3. Check CORS settings in backend
# server/server.ts cors configuration
```

---

## 🎯 Production Deployment

### Environment-Specific Setup

**Development:**
```bash
NODE_ENV=development
npm run dev:all  # Starts everything in dev mode
```

**Staging:**
```bash
NODE_ENV=staging
npm run build
npm run start
```

**Production:**
```bash
NODE_ENV=production
npm run build
npm run start:prod
```

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Start production stack
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Environment Variables for Production

**Required changes:**
```env
NODE_ENV=production

# Use strong passwords
DATABASE_URL="postgresql://user:STRONG_PASSWORD@postgres:5432/github_agent"

# Use production Redis
REDIS_URL="redis://:STRONG_PASSWORD@redis:6379"

# Generate strong webhook secret
GITHUB_WEBHOOK_SECRET="random_string_min_32_chars"

# Use production Ollama (external or scaled)
OLLAMA_BASE_URL="http://ollama.internal:11434"

# SSL in production
FORCE_HTTPS=true
```

---

## 📊 Performance Optimization

### Database Optimization

```bash
# Create indexes for better performance
npx prisma db push --skip-generate

# Vacuum database periodically
docker exec github-agent-postgres-1 vacuumdb -U postgres -d github_agent
```

### Redis Optimization

```bash
# Increase maxmemory in docker-compose.yml
redis:
  command: redis-server --maxmemory 2gb --maxmemory-policy allkeys-lru
```

### Ollama Optimization

```bash
# Use GPU acceleration (if available)
docker-compose.gpu.yml

# Or download models to volume for persistence
docker-compose.yml:
  ollama:
    volumes:
      - ollama_models:/root/.ollama
```

---

## 🔐 Security Hardening

### Production Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Use strong GitHub webhook secret
- [ ] Enable HTTPS/TLS
- [ ] Restrict Docker network access
- [ ] Use environment-specific configs
- [ ] Enable rate limiting
- [ ] Set up monitoring/alerting
- [ ] Regular security updates
- [ ] Backup database regularly

### Secure .env Example

```env
# Never commit this file!
DATABASE_URL="postgresql://secure_user:$(openssl rand -base64 32)@postgres:5432/github_agent"
REDIS_URL="redis://:$(openssl rand -base64 32)@redis:6379"
GITHUB_WEBHOOK_SECRET="$(openssl rand -hex 32)"
JWT_SECRET="$(openssl rand -hex 64)"
```

---

## 📚 Next Steps

After successful installation:

1. **Configure GitHub Webhooks**
   - See: [WEBHOOK-SETUP.md](./docs/WEBHOOK-SETUP.md)

2. **Index Your First Repository**
   - Dashboard → Repositories → Add Repository
   - Wait for indexing to complete

3. **Test with a Real Issue**
   - Create an issue in your repo
   - Label it with "fix-this"
   - Watch the agents work!

4. **Explore the Dashboard**
   - Monitor agent executions
   - Review approval requests
   - Check analytics

5. **Read the Guides**
   - [ROADMAP.md](./ROADMAP.md) - Future features
   - [ARCHITECTURE.md](./ARCHITECTURE.md) - System design
   - [API-DOCS.md](./docs/API-DOCS.md) - API reference

---

## 🆘 Getting Help

### Documentation
- **[README.md](./README.md)** - Project overview
- **[START-HERE.md](./START-HERE.md)** - Quick start
- **[CORPORATE-PROXY-GUIDE.md](./CORPORATE-PROXY-GUIDE.md)** - Proxy issues
- **[TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md)** - Common issues

### Check Logs
```bash
# Backend logs
npm run server

# Worker logs
npm run worker

# Docker logs
docker-compose logs -f

# Specific service
docker-compose logs -f ollama
```

### Verify Setup
```bash
# Run diagnostic script
npm run diagnostic

# Check all services
npm run health-check
```

---

## ✅ Installation Complete!

You should now have:
- ✅ All services running in Docker
- ✅ Database migrated and seeded
- ✅ Backend API responding
- ✅ Task workers processing
- ✅ Frontend dashboard accessible
- ✅ AI model ready

**Access your dashboard at: http://localhost:5173** 🚀

**Next:** Configure your first repository and watch the agents work!
