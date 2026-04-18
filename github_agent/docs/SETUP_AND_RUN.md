# 🚀 GitHub Agent System - Setup & Run Commands

## Prerequisites

- Node.js 18+ and npm
- Docker and Docker Compose
- Git

---

## Step 1: Install Dependencies

```bash
npm install
```

---

## Step 2: Environment Setup

```bash
# Copy example environment file
cp .env.example .env

# Edit .env if needed (defaults should work for local development)
```

Default `.env` works out of the box with Docker Compose defaults.

---

## Step 3: Start Infrastructure (Docker)

```bash
# Start PostgreSQL, Redis, Ollama, ChromaDB
npm run docker:up

# Wait ~30 seconds for services to be healthy
# Check logs (optional):
npm run docker:logs
```

**Services started:**
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`
- Ollama (primary): `localhost:11434`
- ChromaDB: `localhost:8000`

---

## Step 4: Pull Ollama Models

```bash
# In a new terminal, pull required models
docker exec -it github-agent-ollama-1 ollama pull llama3:8b
docker exec -it github-agent-ollama-1 ollama pull nomic-embed-text

# Verify models are downloaded
docker exec -it github-agent-ollama-1 ollama list
```

**Expected output:**
```
NAME                    ID              SIZE
llama3:8b              a6990ed6be41    4.7GB
nomic-embed-text       0a109f422b47    274MB
```

---

## Step 5: Database Setup

```bash
# Generate Prisma client
npm run db:generate

# Run database migrations
npm run db:push
```

---

## Step 6: Start Backend Server

```bash
# Terminal 1: Start Express API server
npm run dev:server
```

**Expected output:**
```
✅ Database connected
✅ Redis connected  
✅ Ollama connected (http://localhost:11434)
🚀 Server running on http://localhost:3001
```

---

## Step 7: Start Frontend Dashboard

```bash
# Terminal 2: Start React frontend
npm run dev
```

**Expected output:**
```
VITE ready in 500 ms

➜  Local:   http://localhost:5173/
```

---

## ✅ System Running

Open browser: **http://localhost:5173**

You should see the GitHub Agent System dashboard.

---

## 🧪 Test the System

### Test 1: Check Ollama

```bash
curl http://localhost:11434/api/tags
```

Should return list of models.

### Test 2: Check Backend Health

```bash
curl http://localhost:3001/health
```

Should return: `{"status": "healthy"}`

### Test 3: Check Services

```bash
# PostgreSQL
docker exec -it github-agent-postgres psql -U postgres -d github_agent -c "SELECT 1;"

# Redis
docker exec -it github-agent-redis redis-cli ping
# Should return: PONG

# ChromaDB
curl http://localhost:8000/api/v1/heartbeat
# Should return: {"nanosecond heartbeat": ...}
```

---

## 🔧 Useful Commands

### View Logs
```bash
# All services
npm run docker:logs

# Specific service
docker logs -f github-agent-postgres
docker logs -f github-agent-redis
docker logs -f github-agent-ollama-1
docker logs -f chromadb
```

### Stop Everything
```bash
# Stop Docker services
npm run docker:down

# Stop backend (Ctrl+C in terminal 1)
# Stop frontend (Ctrl+C in terminal 2)
```

### Restart Services
```bash
# Restart Docker
npm run docker:down
npm run docker:up

# Restart backend
npm run dev:server

# Restart frontend  
npm run dev
```

### Database Management
```bash
# Open Prisma Studio (visual DB editor)
npm run db:studio
# Opens at http://localhost:5555

# Reset database
npm run db:push -- --force-reset
```

---

## 🐛 Troubleshooting

### Issue: "Port already in use"

```bash
# Find and kill process using port 5432, 6379, 11434, or 8000
lsof -ti:5432 | xargs kill -9
lsof -ti:6379 | xargs kill -9
lsof -ti:11434 | xargs kill -9
lsof -ti:8000 | xargs kill -9

# Or stop Docker services
npm run docker:down
```

### Issue: "Cannot connect to database"

```bash
# Check if PostgreSQL is running
docker ps | grep postgres

# Check logs
docker logs github-agent-postgres

# Restart PostgreSQL
docker restart github-agent-postgres
```

### Issue: "Ollama models not found"

```bash
# Check if models are installed
docker exec -it github-agent-ollama-1 ollama list

# If empty, pull models again
docker exec -it github-agent-ollama-1 ollama pull llama3:8b
docker exec -it github-agent-ollama-1 ollama pull nomic-embed-text
```

### Issue: "ChromaDB not responding"

```bash
# Check if running
docker ps | grep chromadb

# Restart ChromaDB
docker restart chromadb

# Check logs
docker logs chromadb
```

---

## 📦 Production Build

```bash
# Build frontend
npm run build

# Build backend
npm run build:server

# Start production server
npm run start:server

# Serve frontend (use nginx or similar)
```

---

## 🧹 Clean Up

```bash
# Stop and remove all containers
npm run docker:down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove node_modules
rm -rf node_modules

# Fresh install
npm install
```

---

## 📊 System Architecture

```
┌─────────────────────────────────────────────┐
│  Frontend (React)       :5173               │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│  Backend API (Express)  :3001               │
├─────────────────────────────────────────────┤
│  • REST API endpoints                       │
│  • WebSocket server (Socket.io)             │
│  • Task queue (BullMQ)                      │
│  • Agent orchestration                      │
└──┬────┬─────┬──────┬──────────┬────────┬───┘
   │    │     │      │          │        │
   │    │     │      │          │        │
   ▼    ▼     ▼      ▼          ▼        ▼
┌──┴─┐ ┌┴──┐ ┌┴───┐ ┌┴─────┐ ┌─┴───┐ ┌──┴──┐
│ PG │ │ R │ │ O  │ │  C   │ │  D  │ │ GH  │
│ SQL│ │ e │ │ l  │ │  h   │ │  o  │ │ API │
│    │ │ d │ │ l  │ │  r   │ │  c  │ │     │
│    │ │ i │ │ a  │ │  o   │ │  k  │ │     │
│    │ │ s │ │ m  │ │  m   │ │  e  │ │     │
│    │ │   │ │ a  │ │  a   │ │  r  │ │     │
└────┘ └───┘ └────┘ └──────┘ └─────┘ └─────┘
:5432  :6379 :11434  :8000    :2375   API
```

---

## 🎯 Quick Start (Copy-Paste)

```bash
# 1. Install
npm install

# 2. Setup env
cp .env.example .env

# 3. Start infrastructure
npm run docker:up

# 4. Wait 30 seconds, then pull models
docker exec -it github-agent-ollama-1 ollama pull llama3:8b
docker exec -it github-agent-ollama-1 ollama pull nomic-embed-text

# 5. Setup database
npm run db:generate
npm run db:push

# 6. Start backend (in terminal 1)
npm run dev:server

# 7. Start frontend (in terminal 2)  
npm run dev

# 8. Open browser
# http://localhost:5173
```

---

## ✅ Success Checklist

- [ ] npm install completed
- [ ] .env file created
- [ ] Docker services running (docker ps shows 4+ containers)
- [ ] Ollama models downloaded (llama3:8b, nomic-embed-text)
- [ ] Database migrated
- [ ] Backend server running on :3001
- [ ] Frontend running on :5173
- [ ] Dashboard accessible in browser

---

## 🆘 Support

If you encounter issues:

1. Check Docker is running: `docker ps`
2. Check logs: `npm run docker:logs`
3. Verify ports are free: `lsof -i :5432,6379,11434,8000,3001,5173`
4. Restart everything: `npm run docker:down && npm run docker:up`
