import { Router } from 'express';
import { codeIndexer } from '../services/rag/codeIndexer';
import { codeSearch } from '../services/rag/codeSearch';
import { vectorStore } from '../services/rag/vectorStore';
import { logger } from '../utils/logger';

export const ragRoutes = Router();

ragRoutes.post('/index/:repoId', async (req, res) => {
  try {
    const repoId = parseInt(req.params.repoId);
    const { repoPath } = req.body;

    logger.info(`Starting indexing for repo ${repoId} at ${repoPath}`);
    
    await codeIndexer.indexRepository(repoPath, repoId);

    res.json({
      success: true,
      message: `Repository ${repoId} indexed successfully`
    });
  } catch (error: any) {
    logger.error('Indexing error:', error);
    res.status(500).json({ error: error.message });
  }
});

ragRoutes.get('/search/definition', async (req, res) => {
  try {
    const { functionName, repoId } = req.query;
    
    if (!functionName || !repoId) {
      return res.status(400).json({ error: 'Missing parameters' });
    }

    const results = await codeSearch.findDefinition(
      functionName as string,
      parseInt(repoId as string)
    );

    res.json({ results });
  } catch (error: any) {
    logger.error('Search error:', error);
    res.status(500).json({ error: error.message });
  }
});

ragRoutes.get('/search/usages', async (req, res) => {
  try {
    const { variableName, repoId } = req.query;
    
    if (!variableName || !repoId) {
      return res.status(400).json({ error: 'Missing parameters' });
    }

    const results = await codeSearch.findUsages(
      variableName as string,
      parseInt(repoId as string)
    );

    res.json({ results });
  } catch (error: any) {
    logger.error('Search error:', error);
    res.status(500).json({ error: error.message });
  }
});

ragRoutes.get('/search/context/:issueId', async (req, res) => {
  try {
    const issueId = parseInt(req.params.issueId);
    
    const { context, sources } = await codeSearch.buildContextForIssue(issueId);

    res.json({ context, sources });
  } catch (error: any) {
    logger.error('Context building error:', error);
    res.status(500).json({ error: error.message });
  }
});

ragRoutes.post('/search/similar', async (req, res) => {
  try {
    const { code, repoId, limit } = req.body;
    
    if (!code || !repoId) {
      return res.status(400).json({ error: 'Missing parameters' });
    }

    const results = await codeSearch.findSimilarCode(
      code,
      parseInt(repoId),
      limit || 5
    );

    res.json({ results });
  } catch (error: any) {
    logger.error('Similarity search error:', error);
    res.status(500).json({ error: error.message });
  }
});

ragRoutes.delete('/clear', async (req, res) => {
  try {
    await vectorStore.clearAll();
    res.json({ success: true, message: 'Vector store cleared' });
  } catch (error: any) {
    logger.error('Clear error:', error);
    res.status(500).json({ error: error.message });
  }
});
