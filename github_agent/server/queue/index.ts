/**
 * Local In-Memory Task Queue
 * Replaces BullMQ + Redis for zero-dependency local execution
 */

import { EventEmitter } from 'events';
import { logger } from '../utils/logger';
import { prisma } from '../index';

class LocalQueue extends EventEmitter {
  private queueName: string;
  private isPaused: boolean = false;

  constructor(name: string) {
    super();
    this.queueName = name;
  }

  async add(name: string, data: any) {
    logger.info(`[Queue: ${this.queueName}] Task added: ${name}`);
    
    // Simulate async queuing
    setImmediate(async () => {
      if (this.isPaused) return;
      this.emit('process', { name, data });
    });

    return { id: Math.random().toString(36).substring(7) };
  }

  async pause() { this.isPaused = true; }
  async resume() { this.isPaused = false; }
  async getWaitingCount() { return 0; }
  async getActiveCount() { return 0; }
  async getCompletedCount() { return 0; }
  async getFailedCount() { return 0; }
  async getDelayedCount() { return 0; }
  async close() {}
}

export const analyzerQueue = new LocalQueue('analyzer');
export const fixerQueue = new LocalQueue('fixer');
export const reviewerQueue = new LocalQueue('reviewer');
export const securityQueue = new LocalQueue('security');
export const testerQueue = new LocalQueue('tester');
export const docsQueue = new LocalQueue('docs');
export const managerQueue = new LocalQueue('manager');
export const indexQueue = new LocalQueue('indexing');

export const queueMap = {
  analyzer: analyzerQueue,
  fixer: fixerQueue,
  reviewer: reviewerQueue,
  security: securityQueue,
  tester: testerQueue,
  docs: docsQueue,
  manager: managerQueue,
  indexing: indexQueue,
};

export async function enqueueTask(agentType: keyof typeof queueMap, taskId: string, data: any) {
  return await queueMap[agentType].add(`${agentType}-task`, { taskId, ...data });
}

export async function getAllQueueStats() {
  return Object.keys(queueMap).map(name => ({
    queueName: name,
    waiting: 0, active: 0, completed: 0, failed: 0, delayed: 0, total: 0
  }));
}

export function setupQueueEvents() {
  logger.info('Local memory queues initialized (Redis removed)');
}
