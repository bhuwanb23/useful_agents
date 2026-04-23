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

---

## Step 3: Start Infrastructure (Docker)

```bash
# Start PostgreSQL, Redis, Ollama, ChromaDB
npm run docker:up

# Wait ~30 seconds for services to be healthy
```

---

## Step 4: Pull Ollama Models

```bash
# Pull required models (using Google Gemma 2)
docker exec -it github-agent-ollama-1 ollama pull gemma2:9b
docker exec -it github-agent-ollama-1 ollama pull nomic-embed-text

# Verify models
docker exec -it github-agent-ollama-1 ollama list
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

---

## Step 7: Start Frontend Dashboard

```bash
# Terminal 2: Start React frontend
npm run dev
```

**Open browser:** `http://localhost:5173`
