import { Router } from 'express';
import { prisma } from '../index';

export const repositoryRoutes = Router();

repositoryRoutes.get('/', async (req, res, next) => {
  try {
    const repos = await prisma.repository.findMany({
      orderBy: { createdAt: 'desc' },
    });
    res.json({ repositories: repos });
  } catch (error) {
    next(error);
  }
});
