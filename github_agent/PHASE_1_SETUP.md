# Phase 1: Foundation & State Management - Setup Guide

## ✅ What's Been Implemented

### 1. **Database Migration** - PostgreSQL + Prisma ORM
- ✅ Complete schema with 12 tables
- ✅ Repositories, Issues, Tasks, Executions, AgentLogs
- ✅ PullRequests, CodeEmbeddings, Prompts
- ✅ OllamaServer pool management
- ✅ SystemConfig for runtime settings
- ✅ Full relational integrity with foreign keys

### 2. **Task Queue** - BullMQ + Redis
- ✅ 7 specialized queues (analyzer, fixer, reviewer, security, tester, docs, manager)
- ✅ Job retries with exponential backoff
- ✅ Priority-based task scheduling
- ✅ Queue statistics and monitoring
- ✅ Pause/resume/clean operations
- ✅ Event listeners for logging

### 3. **Prompt Version Management**
- ✅ Database-backed prompt storage
- ✅ File-based prompt templates (`prompts/` directory)
- ✅ Version control (v1, v2, etc.)
- ✅ Active version switching
- ✅ Caching for performance
- ✅ Example prompts for Analyzer, Fixer, Reviewer

### 4. **Ollama Load Balancer**
- ✅ Multi-instance support
- ✅ Health checking (30s intervals)
- ✅ Automatic failover
- ✅ Least-loaded routing
- ✅ Job tracking per server
- ✅ Response time metrics
- ✅ Capacity management

### 5. **Backend API Server**
- ✅ Express.js with TypeScript
- ✅ 8 API route groups
- ✅ Health check endpoint
- ✅ Error handling middleware
- ✅ Graceful shutdown
- ✅ Structured logging

---

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for development)
- 8GB+ RAM (16GB+ recommended for Ollama)

### 1. Start Infrastructure

```bash
# Start PostgreSQL + Redis + Ollama
docker-compose up -d

# Optional: Start with multiple Ollama instances
docker-compose --profile multi-instance up -d

# Optional: Start with admin tools (pgAdmin, Redis Commander)
docker-compose --profile tools up -d
```

### 2. Setup Environment

```bash
# Copy example environment
cp .env.example .env

# Edit .env with your settings (optional, defaults work for local dev)
```

### 3. Initialize Database

```bash
# Install dependencies
npm install

# Generate Prisma Client
npx prisma generate

# Run migrations (create tables)
npx prisma migrate dev --name init

# Optional: Open Prisma Studio to explore database
npx prisma studio
```

### 4. Pull Ollama Models

```bash
# Pull a model (wait for Ollama to start)
docker exec github-agent-ollama-1 ollama pull llama3:8b

# Or use the smaller model for testing
docker exec github-agent-ollama-1 ollama pull llama3:3b

# If using multiple instances, pull on all
docker exec github-agent-ollama-2 ollama pull llama3:8b
docker exec github-agent-ollama-3 ollama pull llama3:8b
```

### 5. Initialize Prompts

```bash
# Build the server first
npm run build:server

# Initialize prompt manager (loads prompts from files to DB)
node dist/server/scripts/initPrompts.js
```

### 6. Start Backend Server

```bash
# Development mode (with auto-reload)
npm run dev:server

# Production mode
npm run build:server
npm run start:server
```

### 7. Verify Everything Works

```bash
# Check health
curl http://localhost:3001/health

# Should return:
# {
#   "status": "healthy",
#   "timestamp": "2026-...",
#   "uptime": 5.123,
#   "environment": "development",
#   "database": "connected"
# }

# Check Ollama servers
curl http://localhost:3001/api/ollama/servers

# Check agents
curl http://localhost:3001/api/agents

# Check prompts
curl http://localhost:3001/api/prompts
```

---

## 📊 Infrastructure Overview

### Services Running

| Service | Port | Purpose |
|---------|------|---------|
| PostgreSQL | 5432 | Main database |
| Redis | 6379 | Task queue backend |
| Ollama-1 | 11434 | Primary LLM server |
| Ollama-2 | 11435 | Secondary (multi-instance) |
| Ollama-3 | 11436 | Tertiary (multi-instance) |
| Backend API | 3001 | Express server |
| pgAdmin | 5050 | Database UI (tools profile) |
| Redis Commander | 8081 | Redis UI (tools profile) |

### Database Tables

```
repositories       → Monitored GitHub repos
issues             → Tracked GitHub issues
tasks              → Work units for agents
task_dependencies  → Task execution graph
executions         → Agent run history
agent_logs         → LLM thought logs
pull_requests      → Generated PRs
code_embeddings    → RAG vector storage
prompts            → Versioned agent prompts
system_config      → Runtime configuration
ollama_servers     → Load balancer pool
```

### BullMQ Queues

```
analyzer   → Issue classification
fixer      → Code bug fixing
reviewer   → Code review
security   → Vulnerability scanning
tester     → Test generation
docs       → Documentation writing
manager    → Multi-task coordination
```

---

## 🔧 Development Workflow

### Running Prisma Migrations

```bash
# Create a new migration
npx prisma migrate dev --name add_new_field

# Apply migrations to production DB
npx prisma migrate deploy

# Reset database (WARNING: deletes all data)
npx prisma migrate reset
```

### Managing Prompts

```bash
# List all prompts
curl http://localhost:3001/api/prompts

# Get active prompt for fixer agent
curl http://localhost:3001/api/prompts/fixer/active

# Create new prompt version (via API)
curl -X POST http://localhost:3001/api/prompts \
  -H "Content-Type: application/json" \
  -d '{
    "name": "fixer",
    "version": "v2",
    "systemPrompt": "...",
    "userPrompt": "...",
    "isActive": true
  }'
```

### Monitoring Queues

```bash
# Get queue statistics
curl http://localhost:3001/api/agents

# View Redis Commander
open http://localhost:8081

# Use BullBoard (add in next phase)
```

### Ollama Load Balancer

```bash
# Check server health
curl http://localhost:3001/api/ollama/servers

# Trigger manual health check
curl -X POST http://localhost:3001/api/ollama/health-check

# Test generation (direct to load balancer)
curl -X POST http://localhost:3001/api/ollama/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama3:8b",
    "prompt": "Explain async/await in JavaScript"
  }'
```

---

## 📁 Project Structure

```
github-agent-system/
├── prisma/
│   ├── schema.prisma          # Database schema
│   └── migrations/            # Migration history
├── server/
│   ├── index.ts              # Main server entry
│   ├── queue/
│   │   └── index.ts          # BullMQ setup
│   ├── services/
│   │   ├── ollamaLoadBalancer.ts
│   │   └── promptManager.ts
│   ├── routes/               # API endpoints
│   ├── middleware/
│   ├── utils/
│   └── types/
├── prompts/                  # Versioned prompts
│   ├── analyzer/
│   │   ├── v1.txt
│   │   └── v2.txt
│   ├── fixer/
│   └── reviewer/
├── docker-compose.yml        # Infrastructure
├── .env.example
└── package.json
```

---

## 🧪 Testing the System

### 1. Test Database Connection

```typescript
// test-db.ts
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function test() {
  // Create a test repository
  const repo = await prisma.repository.create({
    data: {
      name: 'test-repo',
      owner: 'test-user',
      url: 'https://github.com/test-user/test-repo',
      githubToken: 'test-token',
    },
  });

  console.log('Created repo:', repo);

  // Fetch it back
  const repos = await prisma.repository.findMany();
  console.log('All repos:', repos);
}

test();
```

### 2. Test Queue

```typescript
// test-queue.ts
import { enqueueTask } from './server/queue';

async function test() {
  const job = await enqueueTask('analyzer', 'test-task-123', {
    taskId: 'test-task-123',
    repositoryId: 'repo-id',
    type: 'analyze',
    input: { issueNumber: 42 },
  });

  console.log('Job enqueued:', job.id);
}

test();
```

### 3. Test Ollama Load Balancer

```typescript
// test-ollama.ts
import { ollamaLoadBalancer } from './server/services/ollamaLoadBalancer';

async function test() {
  await ollamaLoadBalancer.initialize();

  const response = await ollamaLoadBalancer.generate({
    model: 'llama3:8b',
    prompt: 'Say hello in 5 words',
  });

  console.log('Response:', response.response);
}

test();
```

---

## 🎯 What's Next (Phase 2)

Phase 1 provides the **skeleton**. Now you can:

1. ✅ Store and retrieve data in PostgreSQL
2. ✅ Queue tasks to Redis via BullMQ
3. ✅ Route LLM requests to available Ollama servers
4. ✅ Version and load prompts dynamically

**Phase 2 Preview**: Implement the actual **Agent Workers** that:
- Listen to queues
- Execute LLM calls with prompts
- Log their "thoughts" to `agent_logs`
- Update task status in real-time
- Handle retries and failures

---

## 🐛 Troubleshooting

### PostgreSQL won't start
```bash
# Check logs
docker logs github-agent-postgres

# Remove old volume
docker-compose down -v
docker-compose up -d postgres
```

### Redis connection refused
```bash
# Ensure Redis is running
docker ps | grep redis

# Test connection
docker exec github-agent-redis redis-cli ping
# Should return: PONG
```

### Ollama is slow/unresponsive
```bash
# Check logs
docker logs github-agent-ollama-1

# Ensure model is pulled
docker exec github-agent-ollama-1 ollama list

# Check GPU usage (if GPU enabled)
nvidia-smi
```

### Prisma migrations fail
```bash
# Reset and re-run
npx prisma migrate reset
npx prisma generate
npx prisma migrate dev
```

---

## 📊 Resource Requirements

### Minimal Setup (1 Ollama instance)
- CPU: 4 cores
- RAM: 8GB (4GB for Ollama + 2GB for services + 2GB for OS)
- Disk: 10GB (models are 3-7GB each)

### Recommended Setup (3 Ollama instances)
- CPU: 8+ cores
- RAM: 24GB (8GB per Ollama + 4GB for services)
- Disk: 20GB
- GPU: NVIDIA RTX 3060+ (optional but 10x faster)

### Production Setup
- CPU: 16+ cores
- RAM: 64GB
- Disk: 100GB SSD
- GPU: NVIDIA A100 or H100
- Postgres: Dedicated server with replication
- Redis: Dedicated cluster

---

## ✅ Phase 1 Checklist

- [x] PostgreSQL schema designed
- [x] Prisma ORM integrated
- [x] BullMQ task queues setup
- [x] Ollama load balancer implemented
- [x] Prompt version management
- [x] Health checking system
- [x] API routes structured
- [x] Docker Compose infrastructure
- [x] Environment configuration
- [x] Example prompts created
- [x] Documentation complete

**Status**: ✅ **PHASE 1 COMPLETE** - Ready for Phase 2 (Agent Implementation)
