/**
 * GitHub Agent System - Backend Server
 * Express API server with BullMQ task queue integration
 */

import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';
import { PrismaClient } from '@prisma/client';
import { agentRoutes } from './routes/agents';
import { taskRoutes } from './routes/tasks';
import { repositoryRoutes } from './routes/repositories';
import { issueRoutes } from './routes/issues';
import { executionRoutes } from './routes/executions';
import { webhookRoutes } from './routes/webhooks';
import { promptRoutes } from './routes/prompts';
import { ollamaRoutes } from './routes/ollama';
import { ragRoutes } from './routes/rag';
import sandboxRoutes from './routes/sandbox.routes';
import managerRoutes from './routes/manager';
import { errorHandler } from './middleware/errorHandler';
import { logger } from './utils/logger';
import { vectorStore } from './services/rag/vectorStore';
import { dockerExecutor } from './services/docker/DockerExecutor';

// Load environment variables
dotenv.config();

// Initialize Prisma Client
export const prisma = new PrismaClient({
  log: process.env.NODE_ENV === 'development' 
    ? ['query', 'error', 'warn'] 
    : ['error'],
});

// Initialize Express app
const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Health check endpoint
app.get('/health', async (req, res) => {
  try {
    // Check database connection
    await prisma.$queryRaw`SELECT 1`;
    
    res.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      uptime: process.uptime(),
      environment: process.env.NODE_ENV,
      database: 'connected',
    });
  } catch (error) {
    res.status(503).json({
      status: 'unhealthy',
      timestamp: new Date().toISOString(),
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

// API Routes
app.use('/api/agents', agentRoutes);
app.use('/api/tasks', taskRoutes);
app.use('/api/repositories', repositoryRoutes);
app.use('/api/issues', issueRoutes);
app.use('/api/executions', executionRoutes);
app.use('/api/webhooks', webhookRoutes);
app.use('/api/prompts', promptRoutes);
app.use('/api/ollama', ollamaRoutes);
app.use('/api/rag', ragRoutes);
app.use('/api/sandbox', sandboxRoutes);
app.use('/api/manager', managerRoutes);

// Error handling
app.use(errorHandler);

// Start server
async function startServer() {
  try {
    // Test database connection
    await prisma.$connect();
    logger.info('✓ Database connected');

    // Initialize vector store
    await vectorStore.initialize();
    logger.info('✓ Vector store initialized');

    // Initialize Docker executor
    await dockerExecutor.initialize();
    logger.info('✓ Docker executor initialized');

    // Start listening
    app.listen(PORT, () => {
      logger.info(`✓ Server running on port ${PORT}`);
      logger.info(`✓ Environment: ${process.env.NODE_ENV}`);
      logger.info(`✓ Health check: http://localhost:${PORT}/health`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
  logger.info('SIGTERM received, shutting down gracefully...');
  await prisma.$disconnect();
  process.exit(0);
});

process.on('SIGINT', async () => {
  logger.info('SIGINT received, shutting down gracefully...');
  await prisma.$disconnect();
  process.exit(0);
});

// Start the server
startServer();
