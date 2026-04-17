import { Router } from 'express';
import { ollamaLoadBalancer } from '../services/ollamaLoadBalancer';

export const ollamaRoutes = Router();

ollamaRoutes.get('/servers', async (req, res, next) => {
  try {
    const stats = await ollamaLoadBalancer.getServerStats();
    res.json({ servers: stats });
  } catch (error) {
    next(error);
  }
});

ollamaRoutes.post('/health-check', async (req, res, next) => {
  try {
    await ollamaLoadBalancer.triggerHealthCheck();
    res.json({ message: 'Health check triggered' });
  } catch (error) {
    next(error);
  }
});
