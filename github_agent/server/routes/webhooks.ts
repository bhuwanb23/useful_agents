import { Router } from 'express';
import { logger } from '../utils/logger';

export const webhookRoutes = Router();

webhookRoutes.post('/github', async (req, res, next) => {
  try {
    const payload = req.body;
    logger.info('GitHub webhook received', { action: payload.action });
    
    // TODO: Process webhook in Phase 2
    
    res.json({ received: true });
  } catch (error) {
    next(error);
  }
});
