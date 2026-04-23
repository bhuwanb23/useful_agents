# 🚀 START HERE - GitHub Agent System

## ✅ Phase 1 Complete - Ready to Run!

This is your **complete setup guide** to get the GitHub Agent System running in under 10 minutes.

---

## 📋 Prerequisites

Before starting, ensure you have:

- ✅ **Docker Desktop** installed and running
- ✅ **Node.js 20+** installed (`node --version`)
- ✅ **8GB+ RAM** available (16GB recommended)
- ✅ **10GB+ disk space** for Ollama models

---

## 🏃 Quick Start (5 Commands)

```bash
# 1. Start infrastructure (PostgreSQL, Redis, Ollama)
docker-compose up -d

# 2. Install dependencies & setup database
npm install
npx prisma generate
npx prisma migrate dev --name init

# 3. Pull Ollama model (takes 2-5 minutes)
docker exec github-agent-ollama-1 ollama pull llama3:8b

# 4. Start backend server (Terminal 1)
npm run dev:server

# 5. Start frontend dashboard (Terminal 2)
npm run dev
```

**Done!** Open http://localhost:5173 in your browser.

---

## 🎯 Step-by-Step Guide

### Step 1: Start Infrastructure

```bash
docker-compose up -d
```

**What this does**:
- Starts PostgreSQL on port 5432
- Starts Redis on port 6379
- Starts Ollama on port 11434

**Verify it worked**:
```bash
docker ps

# You should see 3 containers running:
# - github-agent-postgres
# - github-agent-redis
# - github-agent-ollama-1
```

**Troubleshooting**:
- If containers don't start, run `docker-compose logs` to see errors
- If port conflicts, edit `docker-compose.yml` to change ports

---

### Step 2: Setup Database

```bash
# Install Node.js dependencies
npm install

# Generate Prisma Client (TypeScript types for database)
npx prisma generate

# Create database tables
npx prisma migrate dev --name init
```

**What this does**:
- Installs 300+ npm packages (~1-2 minutes)
- Generates TypeScript types for database access
- Creates 12 tables in PostgreSQL

**Verify it worked**:
```bash
# Open Prisma Studio (database GUI)
npx prisma studio

# Opens http://localhost:5555
# You should see 12 empty tables
```

**Troubleshooting**:
- If `migrate` fails, check PostgreSQL is running: `docker logs github-agent-postgres`
- If port 5432 is busy, another PostgreSQL instance is running

---

### Step 3: Download LLM Model

```bash
# Download Llama 3 8B model (4.7GB)
docker exec github-agent-ollama-1 ollama pull llama3:8b
```

**This takes 2-5 minutes** depending on your internet speed.

**Alternative models**:
```bash
# Smaller/faster (2GB) - good for testing
docker exec github-agent-ollama-1 ollama pull llama3:3b

# Larger/smarter (40GB) - better quality
docker exec github-agent-ollama-1 ollama pull llama3:70b
```

**Verify it worked**:
```bash
docker exec github-agent-ollama-1 ollama list

# Output:
# NAME            ID              SIZE    MODIFIED
# llama3:8b       abc123...       4.7 GB  2 minutes ago
```

**Troubleshooting**:
- If it hangs, Ollama might be starting up. Wait 30 seconds and retry.
- If "connection refused", check: `docker logs github-agent-ollama-1`

---

### Step 4: Start Backend Server

**Open Terminal 1**:
```bash
npm run dev:server
```

**Expected output**:
```
[2026-...] INFO: ✓ Database connected
[2026-...] INFO: ✓ Server running on port 3001
[2026-...] INFO: ✓ Environment: development
[2026-...] INFO: ✓ Health check: http://localhost:3001/health
```

**Verify it worked**:
```bash
# In a new terminal:
curl http://localhost:3001/health

# Should return:
{
  "status": "healthy",
  "timestamp": "2026-...",
  "uptime": 5.123,
  "database": "connected"
}
```

**Troubleshooting**:
- If "port 3001 in use", change `PORT=3002` in `.env`
- If database error, ensure PostgreSQL is running
- If TypeScript errors, run `npm run build:server` first

---

### Step 5: Start Frontend Dashboard

**Open Terminal 2**:
```bash
npm run dev
```

**Expected output**:
```
  VITE v7.2.4  ready in 432 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Open in browser**: http://localhost:5173

**You should see**:
- Header: "🤖 GitHub Agent System"
- Navigation tabs: Dashboard, Repositories, Issues, Agents, etc.
- System overview with placeholder data

---

## ✅ Verify Everything is Working

Run these commands to test each component:

### 1. Check Infrastructure
```bash
# All containers running?
docker ps | grep github-agent

# PostgreSQL healthy?
docker exec github-agent-postgres pg_isready

# Redis healthy?
docker exec github-agent-redis redis-cli ping
# Should return: PONG

# Ollama healthy?
curl http://localhost:11434/api/tags
# Should return JSON with models
```

### 2. Check Backend API
```bash
# Health check
curl http://localhost:3001/health

# Agent queues
curl http://localhost:3001/api/agents

# Ollama servers
curl http://localhost:3001/api/ollama/servers

# Should show 1 server, isHealthy: true
```

### 3. Check Database
```bash
# Open Prisma Studio
npx prisma studio

# Go to http://localhost:5555
# Click on "Repository" table
# Should be empty but accessible
```

### 4. Check Frontend
- Open http://localhost:5173
- Click through all tabs (Dashboard, Repos, Issues, Agents, etc.)
- All should load without errors

---

## 🎮 Next Steps - Try It Out!

### Option 1: Explore the UI

The frontend shows **mock data** to demonstrate the interface:
- **Dashboard**: System stats, recent issues, active executions
- **Repositories**: Would show connected GitHub repos
- **Issues**: Tracked GitHub issues
- **Agents**: Status of 7 AI agents
- **Executions**: Real-time agent activity logs
- **Approvals**: Human-in-the-loop review workflow

### Option 2: Create Test Data

```bash
# Open Prisma Studio
npx prisma studio

# Go to "Repository" table → "Add Record"
# Fill in:
name: "test-repo"
owner: "your-username"
url: "https://github.com/your-username/test-repo"
githubToken: "your-github-token"

# Save → You'll see it in the database
```

### Option 3: Test Ollama

```bash
# Direct API call to Ollama
curl http://localhost:11434/api/generate -d '{
  "model": "llama3:8b",
  "prompt": "Say hello in 5 words",
  "stream": false
}'

# Should return JSON with "response" field
```

### Option 4: Test Load Balancer

```bash
# Call through the load balancer
curl -X POST http://localhost:3001/api/ollama/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "prompt": "Explain async/await in one sentence"
  }'
```

---

## 📚 Learn More

### Documentation

| File | What's Inside |
|------|---------------|
| `PHASE_1_SETUP.md` | Detailed setup guide (600 lines) |
| `PHASE_1_COMPLETE.md` | What was built in Phase 1 |
| `ARCHITECTURE.md` | Technical architecture |
| `ROADMAP.md` | 10-phase implementation plan |
| `README.md` | Project overview |

### Key Directories

```
github-agent-system/
├── server/              # Backend API (TypeScript)
│   ├── routes/         # API endpoints
│   ├── services/       # Ollama, Prompts
│   └── queue/          # BullMQ setup
├── prisma/
│   └── schema.prisma   # Database schema (12 tables)
├── prompts/            # Versioned agent prompts
│   ├── analyzer/
│   ├── fixer/
│   └── reviewer/
├── src/                # Frontend React app
└── docker-compose.yml  # Infrastructure
```

---

## 🔧 Common Commands

### Infrastructure
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart ollama-1
```

### Database
```bash
# Open database GUI
npx prisma studio

# View database in terminal
docker exec -it github-agent-postgres psql -U postgres -d github_agent

# Reset database (WARNING: deletes all data)
npx prisma migrate reset
```

### Development
```bash
# Backend (Terminal 1)
npm run dev:server

# Frontend (Terminal 2)
npm run dev

# Build for production
npm run build        # Frontend
npm run build:server # Backend
```

---

## 🐛 Troubleshooting

### "Port already in use"

```bash
# Find what's using the port
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
lsof -i :11434 # Ollama
lsof -i :3001  # Backend

# Kill the process or change port in docker-compose.yml
```

### "Cannot connect to database"

```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs github-agent-postgres

# Restart it
docker-compose restart postgres

# Verify connection
docker exec -it github-agent-postgres psql -U postgres -c "SELECT 1"
```

### "Ollama model not found"

```bash
# List models
docker exec github-agent-ollama-1 ollama list

# Pull again
docker exec github-agent-ollama-1 ollama pull llama3:8b

# Check logs
docker logs github-agent-ollama-1
```

### "npm install fails"

```bash
# Clear cache
rm -rf node_modules package-lock.json
npm cache clean --force

# Reinstall
npm install

# If still fails, check Node version
node --version  # Should be 20+
```

---

## 💡 Tips

### Speed Up Ollama

If you have an NVIDIA GPU:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)
2. Uncomment GPU section in `docker-compose.yml`
3. Restart: `docker-compose up -d ollama-1`

**Result**: 10x faster inference (200 tokens/sec → 2000 tokens/sec)

### Run Multiple Ollama Instances

```bash
# Start with 3 Ollama servers
docker-compose --profile multi-instance up -d

# Pull model on all 3
docker exec github-agent-ollama-1 ollama pull llama3:8b
docker exec github-agent-ollama-2 ollama pull llama3:8b
docker exec github-agent-ollama-3 ollama pull llama3:8b

# Check load balancer
curl http://localhost:3001/api/ollama/servers
# Should show 3 servers
```

### Use Admin Tools

```bash
# Start pgAdmin + Redis Commander
docker-compose --profile tools up -d

# PostgreSQL Admin: http://localhost:5050
# Login: admin@github-agent.local / admin

# Redis Admin: http://localhost:8081
```

---

## ✅ Success Checklist

Before moving to Phase 2, verify:

- [ ] ✅ Docker containers running (3-5 depending on setup)
- [ ] ✅ PostgreSQL accessible via Prisma Studio
- [ ] ✅ Redis responding to `PING` command
- [ ] ✅ Ollama model downloaded (`ollama list`)
- [ ] ✅ Backend server starts without errors
- [ ] ✅ Health check returns `"status": "healthy"`
- [ ] ✅ Frontend loads at http://localhost:5173
- [ ] ✅ All navigation tabs work
- [ ] ✅ Can create test data in Prisma Studio
- [ ] ✅ Load balancer shows healthy servers

---

## 🎉 You're Ready!

**Phase 1 Status**: ✅ **COMPLETE AND RUNNING**

You now have:
- ✅ PostgreSQL database with 12 tables
- ✅ Redis task queue
- ✅ Ollama LLM with load balancing
- ✅ Backend API server
- ✅ Frontend dashboard
- ✅ Versioned prompt system

**What to do now**:

1. **Explore**: Click around the UI, check the code
2. **Read**: Open `PHASE_1_COMPLETE.md` to see what was built
3. **Plan**: Review `ROADMAP.md` for Phase 2 (Agent Implementation)
4. **Experiment**: Try API calls, create test data, tweak prompts

**Ready for Phase 2?** Let me know and I'll implement the agent workers that will actually process tasks from the queues!

---

**Questions?** Check the documentation files or ask for help.

**Happy hacking!** 🚀
