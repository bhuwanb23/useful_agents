import express from 'express';
import { ManagerAgent, ExecutionPlan } from '../services/ManagerAgent';
import { MultiFilePRService } from '../services/MultiFilePRService';

const router = express.Router();
const manager = new ManagerAgent();

/**
 * POST /api/manager/plan
 * Create execution plan for an issue
 */
router.post('/plan', async (req, res) => {
  try {
    const { repositoryId, issueId, issueTitle, issueBody } = req.body;

    if (!repositoryId || !issueId || !issueTitle || !issueBody) {
      return res.status(400).json({
        error: 'Missing required fields',
      });
    }

    const plan = await manager.createExecutionPlan(
      repositoryId,
      issueId,
      issueTitle,
      issueBody
    );

    res.json({
      success: true,
      plan,
    });
  } catch (error: any) {
    console.error('[Manager API] Plan creation failed:', error);
    res.status(500).json({
      error: 'Failed to create execution plan',
      details: error.message,
    });
  }
});

/**
 * POST /api/manager/execute/:planId
 * Execute a plan
 */
router.post('/execute/:planId', async (req, res) => {
  try {
    const { planId } = req.params;

    // Start execution in background
    manager.executePlan(planId).catch(err => {
      console.error(`[Manager API] Plan execution failed: ${err.message}`);
    });

    res.json({
      success: true,
      message: 'Plan execution started',
      planId,
    });
  } catch (error: any) {
    console.error('[Manager API] Execute request failed:', error);
    res.status(500).json({
      error: 'Failed to start plan execution',
      details: error.message,
    });
  }
});

/**
 * GET /api/manager/plan/:planId
 * Get plan details
 */
router.get('/plan/:planId', async (req, res) => {
  try {
    const { planId } = req.params;
    
    // This would fetch from database
    res.json({
      success: true,
      plan: {
        id: planId,
        status: 'pending',
        // ... plan details
      },
    });
  } catch (error: any) {
    console.error('[Manager API] Get plan failed:', error);
    res.status(500).json({
      error: 'Failed to get plan',
      details: error.message,
    });
  }
});

/**
 * POST /api/manager/pr/create
 * Create multi-file PR
 */
router.post('/pr/create', async (req, res) => {
  try {
    const { owner, repo, branchName, metadata, accessToken, draft } = req.body;

    if (!owner || !repo || !branchName || !metadata) {
      return res.status(400).json({
        error: 'Missing required fields',
      });
    }

    const prService = new MultiFilePRService(accessToken);

    // Validate PR first
    const validation = await prService.validatePR(metadata);
    if (!validation.valid) {
      return res.status(400).json({
        error: 'PR validation failed',
        details: validation.errors,
      });
    }

    // Create PR (draft or normal)
    const result = draft
      ? await prService.createDraftPR(owner, repo, branchName, metadata)
      : await prService.createMultiFilePR(owner, repo, branchName, metadata);

    res.json({
      success: true,
      prNumber: result.prNumber,
      prUrl: result.prUrl,
    });
  } catch (error: any) {
    console.error('[Manager API] PR creation failed:', error);
    res.status(500).json({
      error: 'Failed to create PR',
      details: error.message,
    });
  }
});

/**
 * POST /api/manager/pr/:prNumber/comment
 * Add execution report comment to PR
 */
router.post('/pr/:prNumber/comment', async (req, res) => {
  try {
    const { prNumber } = req.params;
    const { owner, repo, executionDetails, accessToken } = req.body;

    const prService = new MultiFilePRService(accessToken);
    
    await prService.addExecutionComment(
      owner,
      repo,
      parseInt(prNumber),
      executionDetails
    );

    res.json({
      success: true,
      message: 'Comment added to PR',
    });
  } catch (error: any) {
    console.error('[Manager API] Add comment failed:', error);
    res.status(500).json({
      error: 'Failed to add comment',
      details: error.message,
    });
  }
});

export default router;
