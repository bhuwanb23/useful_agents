/**
 * Agent routes - GET agent status and metrics
 */

import { Router } from 'express';
import { getAllQueueStats } from '../queue';
import { logger } from '../utils/logger';

export const agentRoutes = Router();

/**
 * GET /api/agents - List all agents with status
 */
agentRoutes.get('/', async (req, res, next) => {
  try {
    const queueStats = await getAllQueueStats();
    
    const agents = queueStats.map(stat => ({
      type: stat.queueName,
      status: stat.active > 0 ? 'busy' : 'idle',
      capabilities: getAgentCapabilities(stat.queueName),
      metrics: {
        waiting: stat.waiting,
        active: stat.active,
        completed: stat.completed,
        failed: stat.failed,
      },
    }));

    res.json({ agents });
  } catch (error) {
    next(error);
  }
});

function getAgentCapabilities(agentType: string): string[] {
  const capabilities: Record<string, string[]> = {
    analyzer: ['Issue classification', 'Priority assessment', 'Complexity estimation'],
    fixer: ['Code generation', 'Bug fixing', 'Self-correction', 'Dependency management'],
    reviewer: ['Code quality checks', 'Best practices', 'Security review', 'Test coverage'],
    security: ['Vulnerability scanning', 'CVE checking', 'Secret detection', 'Dependency audit'],
    tester: ['Unit test generation', 'Integration tests', 'Coverage analysis', 'Test execution'],
    docs: ['Documentation generation', 'README updates', 'API docs', 'Code comments'],
    manager: ['Task planning', 'Dependency orchestration', 'Multi-file coordination'],
  };

  return capabilities[agentType] || [];
}
