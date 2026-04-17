import { Router } from 'express';
import { containerManager } from '../services/docker/containerManager';
import { logger } from '../utils/logger';

export const dockerRoutes = Router();

dockerRoutes.post('/validate', async (req, res) => {
  try {
    const { code, filePath, language } = req.body;

    if (!code || !filePath || !language) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }

    const result = await containerManager.validateCode(code, filePath, language);

    res.json(result);
  } catch (error: any) {
    logger.error('Validation error:', error);
    res.status(500).json({ error: error.message });
  }
});

dockerRoutes.post('/test', async (req, res) => {
  try {
    const { repoPath, language } = req.body;

    if (!repoPath || !language) {
      return res.status(400).json({ error: 'Missing required parameters' });
    }

    const result = await containerManager.runTests(repoPath, language);

    res.json(result);
  } catch (error: any) {
    logger.error('Test execution error:', error);
    res.status(500).json({ error: error.message });
  }
});

dockerRoutes.post('/cleanup', async (req, res) => {
  try {
    await containerManager.cleanupOldContainers();
    res.json({ success: true, message: 'Cleanup completed' });
  } catch (error: any) {
    logger.error('Cleanup error:', error);
    res.status(500).json({ error: error.message });
  }
});
