import { Router } from 'express';
import { prisma } from '../index';

export const executionRoutes = Router();

executionRoutes.get('/', async (req, res, next) => {
  try {
    const executions = await prisma.execution.findMany({
      take: 50,
      orderBy: { startedAt: 'desc' },
      include: {
        task: {
          include: {
            repository: { select: { name: true, owner: true } },
            issue: { select: { number: true, title: true } },
          },
        },
        logs: {
          orderBy: { timestamp: 'asc' },
          take: 10,
        },
      },
    });
    res.json({ executions });
  } catch (error) {
    next(error);
  }
});
