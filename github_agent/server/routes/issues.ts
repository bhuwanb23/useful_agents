import { Router } from 'express';
import { prisma } from '../index';

export const issueRoutes = Router();

issueRoutes.get('/', async (req, res, next) => {
  try {
    const issues = await prisma.issue.findMany({
      take: 100,
      orderBy: { createdAt: 'desc' },
      include: {
        repository: { select: { name: true, owner: true } },
      },
    });
    res.json({ issues });
  } catch (error) {
    next(error);
  }
});
