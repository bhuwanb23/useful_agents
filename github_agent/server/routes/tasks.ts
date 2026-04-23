import { Router } from 'express';
import { prisma } from '../index';

export const taskRoutes = Router();

taskRoutes.get('/', async (req, res, next) => {
  try {
    const tasks = await prisma.task.findMany({
      take: 100,
      orderBy: { queuedAt: 'desc' },
      include: {
        repository: { select: { name: true, owner: true } },
        issue: { select: { number: true, title: true } },
      },
    });
    res.json({ tasks });
  } catch (error) {
    next(error);
  }
});
