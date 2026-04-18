import { Router } from 'express';
import { dockerExecutor } from '../services/docker/DockerExecutor';
import { testRunner } from '../services/docker/TestRunner';
import { codeFixerAgent } from '../services/agents/CodeFixerAgent';
import { logger } from '../utils/logger';

const router = Router();

// Execute code in sandbox
router.post('/execute', async (req, res) => {
  try {
    const { code, language, timeout = 30000, additionalFiles } = req.body;

    if (!code || !language) {
      return res.status(400).json({ error: 'Code and language are required' });
    }

    const result = await dockerExecutor.executeCode(
      code,
      {
        language,
        timeout,
        memory: 512,
        cpus: 1,
        networkEnabled: false,
      },
      additionalFiles
    );

    res.json(result);
  } catch (error) {
    logger.error('Code execution error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Execution failed' });
  }
});

// Run tests
router.post('/test', async (req, res) => {
  try {
    const { repoPath, language, testCommand, timeout = 300000 } = req.body;

    if (!repoPath || !language) {
      return res.status(400).json({ error: 'Repository path and language are required' });
    }

    const result = await testRunner.runTests({
      repoPath,
      language,
      testCommand,
      timeout,
    });

    res.json(result);
  } catch (error) {
    logger.error('Test execution error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Test failed' });
  }
});

// Run tests with retry
router.post('/test/retry', async (req, res) => {
  try {
    const { repoPath, language, testCommand, retries = 3 } = req.body;

    if (!repoPath || !language) {
      return res.status(400).json({ error: 'Repository path and language are required' });
    }

    const result = await testRunner.runTestsWithRetry({
      repoPath,
      language,
      testCommand,
      retries,
    });

    res.json(result);
  } catch (error) {
    logger.error('Test retry error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Test failed' });
  }
});

// Validate code changes
router.post('/validate', async (req, res) => {
  try {
    const { repoPath, modifiedFiles, language } = req.body;

    if (!repoPath || !modifiedFiles || !language) {
      return res.status(400).json({ error: 'Repository path, modified files, and language are required' });
    }

    const filesMap = new Map(Object.entries(modifiedFiles));
    const result = await testRunner.validateCodeChange(repoPath, filesMap, language);

    res.json(result);
  } catch (error) {
    logger.error('Validation error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Validation failed' });
  }
});

// Get test coverage
router.post('/coverage', async (req, res) => {
  try {
    const { repoPath, language } = req.body;

    if (!repoPath || !language) {
      return res.status(400).json({ error: 'Repository path and language are required' });
    }

    const result = await testRunner.getTestCoverage(repoPath, language);
    res.json(result);
  } catch (error) {
    logger.error('Coverage error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Coverage check failed' });
  }
});

// Fix code with self-correction
router.post('/fix', async (req, res) => {
  try {
    const {
      taskId,
      issueId,
      repoPath,
      issueTitle,
      issueBody,
      language,
      relevantFiles,
    } = req.body;

    if (!taskId || !issueId || !repoPath || !issueTitle || !issueBody || !language) {
      return res.status(400).json({ error: 'Missing required fields' });
    }

    const result = await codeFixerAgent.fix({
      taskId,
      issueId,
      repoPath,
      issueTitle,
      issueBody,
      language,
      relevantFiles,
    });

    res.json(result);
  } catch (error) {
    logger.error('Fix error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Fix failed' });
  }
});

// Quick fix for single file
router.post('/quick-fix', async (req, res) => {
  try {
    const { filePath, errorMessage, language } = req.body;

    if (!filePath || !errorMessage || !language) {
      return res.status(400).json({ error: 'File path, error message, and language are required' });
    }

    const fixedCode = await codeFixerAgent.quickFix(filePath, errorMessage, language);
    res.json({ fixedCode });
  } catch (error) {
    logger.error('Quick fix error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Quick fix failed' });
  }
});

// Get container stats
router.get('/containers', async (req, res) => {
  try {
    const stats = await dockerExecutor.getContainerStats();
    res.json({ containers: stats });
  } catch (error) {
    logger.error('Container stats error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Failed to get stats' });
  }
});

// Cleanup all containers
router.post('/cleanup', async (req, res) => {
  try {
    await dockerExecutor.cleanupAll();
    res.json({ message: 'Cleanup complete' });
  } catch (error) {
    logger.error('Cleanup error:', error);
    res.status(500).json({ error: error instanceof Error ? error.message : 'Cleanup failed' });
  }
});

// Health check
router.get('/health', async (req, res) => {
  try {
    const stats = await dockerExecutor.getContainerStats();
    res.json({
      status: 'healthy',
      activeContainers: stats.length,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    res.status(500).json({
      status: 'unhealthy',
      error: error instanceof Error ? error.message : 'Unknown error',
    });
  }
});

export default router;
