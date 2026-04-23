import { Router } from 'express';
import { promptManager } from '../services/promptManager';

export const promptRoutes = Router();

promptRoutes.get('/', async (req, res, next) => {
  try {
    const { agentType } = req.query;
    const prompts = await promptManager.listPrompts(agentType as string);
    res.json({ prompts });
  } catch (error) {
    next(error);
  }
});

promptRoutes.get('/:agentType/active', async (req, res, next) => {
  try {
    const prompt = await promptManager.getActivePrompt(req.params.agentType);
    res.json({ prompt });
  } catch (error) {
    next(error);
  }
});
