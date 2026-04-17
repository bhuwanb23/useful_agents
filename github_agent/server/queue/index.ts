/**
 * BullMQ Task Queue Configuration
 * Replaces Celery + Redis for Node.js
 */

import { Queue, Worker, QueueEvents, Job } from 'bullmq';
import { Redis } from 'ioredis';
import { logger } from '../utils/logger';
import type { AgentTask } from '../types';

// Redis connection
const redisConnection = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD || undefined,
  maxRetriesPerRequest: null,
});

// Queue configuration
const defaultQueueOptions = {
  connection: redisConnection,
  defaultJobOptions: {
    attempts: 3,
    backoff: {
      type: 'exponential' as const,
      delay: 2000,
    },
    removeOnComplete: {
      count: 100,
      age: 3600, // 1 hour
    },
    removeOnFail: {
      count: 500,
      age: 86400, // 24 hours
    },
  },
};

// ===== AGENT QUEUES =====

export const analyzerQueue = new Queue('analyzer', defaultQueueOptions);
export const fixerQueue = new Queue('fixer', defaultQueueOptions);
export const reviewerQueue = new Queue('reviewer', defaultQueueOptions);
export const securityQueue = new Queue('security', defaultQueueOptions);
export const testerQueue = new Queue('tester', defaultQueueOptions);
export const docsQueue = new Queue('docs', defaultQueueOptions);
export const managerQueue = new Queue('manager', {
  ...defaultQueueOptions,
  defaultJobOptions: {
    ...defaultQueueOptions.defaultJobOptions,
    priority: 10, // Manager tasks get high priority
  },
});

// Map agent types to queues
export const queueMap = {
  analyzer: analyzerQueue,
  fixer: fixerQueue,
  reviewer: reviewerQueue,
  security: securityQueue,
  tester: testerQueue,
  docs: docsQueue,
  manager: managerQueue,
} as const;

// ===== QUEUE HELPERS =====

/**
 * Add a task to the appropriate agent queue
 */
export async function enqueueTask(
  agentType: keyof typeof queueMap,
  taskId: string,
  data: AgentTask,
  options?: {
    priority?: number;
    delay?: number;
    attempts?: number;
  }
) {
  const queue = queueMap[agentType];
  
  if (!queue) {
    throw new Error(`Unknown agent type: ${agentType}`);
  }

  const job = await queue.add(
    `${agentType}-task`,
    {
      taskId,
      agentType,
      ...data,
    },
    {
      jobId: taskId,
      priority: options?.priority,
      delay: options?.delay,
      attempts: options?.attempts,
    }
  );

  logger.info(`Task enqueued: ${taskId} -> ${agentType} queue (Job ID: ${job.id})`);
  return job;
}

/**
 * Get queue statistics
 */
export async function getQueueStats(queueName: keyof typeof queueMap) {
  const queue = queueMap[queueName];
  
  const [waiting, active, completed, failed, delayed] = await Promise.all([
    queue.getWaitingCount(),
    queue.getActiveCount(),
    queue.getCompletedCount(),
    queue.getFailedCount(),
    queue.getDelayedCount(),
  ]);

  return {
    queueName,
    waiting,
    active,
    completed,
    failed,
    delayed,
    total: waiting + active + completed + failed + delayed,
  };
}

/**
 * Get all queue statistics
 */
export async function getAllQueueStats() {
  const stats = await Promise.all(
    Object.keys(queueMap).map(name => 
      getQueueStats(name as keyof typeof queueMap)
    )
  );
  
  return stats;
}

/**
 * Pause a queue (stop processing)
 */
export async function pauseQueue(queueName: keyof typeof queueMap) {
  const queue = queueMap[queueName];
  await queue.pause();
  logger.info(`Queue paused: ${queueName}`);
}

/**
 * Resume a queue
 */
export async function resumeQueue(queueName: keyof typeof queueMap) {
  const queue = queueMap[queueName];
  await queue.resume();
  logger.info(`Queue resumed: ${queueName}`);
}

/**
 * Clean up old jobs from a queue
 */
export async function cleanQueue(
  queueName: keyof typeof queueMap,
  grace: number = 3600000 // 1 hour in ms
) {
  const queue = queueMap[queueName];
  
  await Promise.all([
    queue.clean(grace, 100, 'completed'),
    queue.clean(grace * 24, 100, 'failed'), // Keep failed for 24 hours
  ]);
  
  logger.info(`Queue cleaned: ${queueName}`);
}

// ===== QUEUE EVENTS =====

/**
 * Setup global queue event listeners
 */
export function setupQueueEvents() {
  Object.entries(queueMap).forEach(([name, queue]) => {
    const events = new QueueEvents(name, { connection: redisConnection });

    events.on('completed', ({ jobId, returnvalue }) => {
      logger.info(`Job completed: ${jobId} in queue ${name}`);
    });

    events.on('failed', ({ jobId, failedReason }) => {
      logger.error(`Job failed: ${jobId} in queue ${name}`, { failedReason });
    });

    events.on('progress', ({ jobId, data }) => {
      logger.debug(`Job progress: ${jobId} in queue ${name}`, { progress: data });
    });

    events.on('stalled', ({ jobId }) => {
      logger.warn(`Job stalled: ${jobId} in queue ${name}`);
    });
  });

  logger.info('Queue event listeners initialized');
}

// ===== GRACEFUL SHUTDOWN =====

export async function closeQueues() {
  logger.info('Closing all queues...');
  
  await Promise.all([
    ...Object.values(queueMap).map(q => q.close()),
    redisConnection.quit(),
  ]);
  
  logger.info('All queues closed');
}

// Handle shutdown
process.on('SIGTERM', closeQueues);
process.on('SIGINT', closeQueues);
