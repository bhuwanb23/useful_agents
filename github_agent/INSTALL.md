# Installation Guide

## Prerequisites

- Node.js 18+ and npm
- Docker and Docker Compose
- PostgreSQL (or use Docker)
- Git

## Step-by-Step Installation

### 1. Install Dependencies

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
```

If you encounter errors with specific packages:

```bash
# Install with legacy peer deps (recommended)
npm install --legacy-peer-deps
```

### 2. Setup Environment

```bash
# Copy example env
cp server/.env.example server/.env

# Edit the file with your settings
nano server/.env
```

Required environment variables:
```env
DATABASE_URL="postgresql://postgres:postgres@localhost:5432/github_agent"
REDIS_URL="redis://localhost:6379"
OLLAMA_BASE_URL="http://localhost:11434"
CHROMADB_HOST="localhost"
CHROMADB_PORT="8000"
```

### 3. Start Infrastructure (Docker)

```bash
# Start PostgreSQL, Redis, ChromaDB
npm run docker:up

# Check if all containers are running
docker ps
```

You should see:
- `github-agent-postgres`
- `github-agent-redis`
- `github-agent-chromadb`

### 4. Setup Database

```bash
# Generate Prisma client
npm run db:generate

# Run migrations
npm run db:migrate

# (Optional) Open Prisma Studio to view DB
npm run db:studio
```

### 5. Install and Start Ollama

```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull llama3.1:8b
ollama pull nomic-embed-text

# Verify Ollama is running
curl http://localhost:11434/api/tags
```

### 6. Start the Application

```bash
# Terminal 1: Start backend server
npm run dev:server

# Terminal 2: Start frontend dev server
npm run dev
```

### 7. Verify Installation

Open your browser:
- Frontend: http://localhost:5173
- Backend API: http://localhost:3001/health
- Prisma Studio: http://localhost:5555 (if running)

Test the API:
```bash
# Health check
curl http://localhost:3001/health

# Check Ollama connection
curl http://localhost:3001/api/ollama/health
```

## Common Issues

### Issue: npm install fails with peer dependency conflicts

**Solution:**
```bash
npm install --legacy-peer-deps
```

### Issue: Prisma client not found

**Solution:**
```bash
npm run db:generate
```

### Issue: Docker containers won't start

**Solution:**
```bash
# Stop all containers
npm run docker:down

# Remove volumes and restart
docker-compose down -v
npm run docker:up
```

### Issue: Ollama not responding

**Solution:**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve

# In another terminal, pull models
ollama pull llama3.1:8b
```

### Issue: ChromaDB connection errors

**Solution:**
```bash
# Check ChromaDB logs
docker logs github-agent-chromadb

# Restart ChromaDB
docker restart github-agent-chromadb
```

### Issue: TypeScript errors in IDE

**Solution:**
```bash
# Reload TypeScript server in VS Code
# Press Cmd+Shift+P (Mac) or Ctrl+Shift+P (Windows)
# Type "TypeScript: Restart TS Server"

# Or reload window
# Cmd+Shift+P > "Developer: Reload Window"
```

## Production Build

```bash
# Build frontend
npm run build

# Build backend
npm run build:server

# Start production server
npm run start:server
```

## Development Workflow

```bash
# Start infrastructure
npm run docker:up

# Terminal 1: Backend with auto-reload
npm run dev:server

# Terminal 2: Frontend with hot reload
npm run dev

# Terminal 3: View Docker logs
npm run docker:logs

# Terminal 4: Monitor Redis/queues
redis-cli monitor
```

## Next Steps

After installation, proceed to:
1. Configure a GitHub repository in the UI
2. Add a GitHub access token
3. Test the agent with a simple issue
4. Monitor the execution in real-time

See `ROADMAP.md` for feature implementation phases.
