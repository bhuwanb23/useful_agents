import dotenv from 'dotenv';

dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3001', 10),
  nodeEnv: process.env.NODE_ENV || 'development',
  
  // Database
  databaseUrl: process.env.DATABASE_URL || 'postgresql://postgres:postgres@localhost:5432/github_agent',
  
  // Redis
  redisUrl: process.env.REDIS_URL || 'redis://localhost:6379',
  
  // Ollama
  ollamaUrl: process.env.OLLAMA_URL || 'http://localhost:11434',
  ollamaModel: process.env.OLLAMA_MODEL || 'llama3.2',
  
  // ChromaDB
  chromaUrl: process.env.CHROMA_URL || 'http://localhost:8000',
  
  // GitHub
  githubToken: process.env.GITHUB_TOKEN || '',
  githubWebhookSecret: process.env.GITHUB_WEBHOOK_SECRET || '',
};
