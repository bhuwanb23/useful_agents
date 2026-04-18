import { AgentConfig } from '../types';

// Agent Configuration - Defines capabilities and personas for each agent
export const AGENT_CONFIGS: Record<string, AgentConfig> = {
  analyzer: {
    type: 'analyzer',
    name: 'Issue Analyzer',
    description: 'Classifies and analyzes GitHub issues, links related issues',
    capabilities: [
      'Issue classification (bug/feature/security)',
      'Severity assessment',
      'Related issue detection',
      'Dependency analysis'
    ],
    model: 'ollama:llama3',
    maxRetries: 2,
    timeout: 30000
  },
  
  fixer: {
    type: 'fixer',
    name: 'Code Fixer',
    description: 'Writes and modifies code to fix bugs and implement features',
    capabilities: [
      'Code generation',
      'Bug fixing',
      'Feature implementation',
      'Dependency installation',
      'Multi-file changes'
    ],
    model: 'ollama:codellama',
    maxRetries: 3,
    timeout: 60000
  },
  
  reviewer: {
    type: 'reviewer',
    name: 'Code Reviewer',
    description: 'Reviews code changes for quality, correctness, and best practices',
    capabilities: [
      'Code quality analysis',
      'Best practices verification',
      'Performance review',
      'Sandbox execution',
      'Test validation'
    ],
    model: 'ollama:llama3',
    maxRetries: 2,
    timeout: 45000
  },
  
  security: {
    type: 'security',
    name: 'Security Scanner',
    description: 'Scans code for vulnerabilities and security issues',
    capabilities: [
      'Vulnerability detection',
      'CVE database checking',
      'Dependency security audit',
      'Secret detection',
      'OWASP compliance'
    ],
    model: 'ollama:llama3',
    maxRetries: 2,
    timeout: 40000
  },
  
  test_writer: {
    type: 'test_writer',
    name: 'Test Writer',
    description: 'Generates comprehensive unit and integration tests',
    capabilities: [
      'Unit test generation',
      'Integration test creation',
      'Code coverage analysis',
      'Edge case detection',
      'Test framework setup'
    ],
    model: 'ollama:codellama',
    maxRetries: 3,
    timeout: 50000
  },
  
  docs_writer: {
    type: 'docs_writer',
    name: 'Documentation Writer',
    description: 'Creates and updates documentation automatically',
    capabilities: [
      'README updates',
      'API documentation',
      'Docstring generation',
      'Changelog updates',
      'Documentation site generation'
    ],
    model: 'ollama:llama3',
    maxRetries: 2,
    timeout: 35000
  },
  
  manager: {
    type: 'manager',
    name: 'Planning Manager',
    description: 'Creates execution plans for complex multi-step tasks',
    capabilities: [
      'Task decomposition',
      'Dependency mapping',
      'Execution planning',
      'Agent orchestration',
      'Progress monitoring'
    ],
    model: 'ollama:llama3',
    maxRetries: 2,
    timeout: 40000
  }
};

// System Configuration
export const SYSTEM_CONFIG = {
  maxConcurrentTasks: 10,
  defaultMaxRetries: 3,
  taskTimeout: 300000, // 5 minutes
  enableSandbox: true,
  enableRAG: true,
  enableHumanApproval: true,
  ragVectorDatabase: 'chromadb',
  messageQueueType: 'redis',
  memoryDatabase: 'sqlite',
  realtimeUpdates: true
};

// Event Types for Message Bus
export const EVENT_TYPES = {
  TASK_CREATED: 'task.created',
  TASK_STARTED: 'task.started',
  TASK_COMPLETED: 'task.completed',
  TASK_FAILED: 'task.failed',
  
  AGENT_STARTED: 'agent.started',
  AGENT_COMPLETED: 'agent.completed',
  AGENT_FAILED: 'agent.failed',
  
  FIX_COMPLETED: 'fix.completed',
  REVIEW_COMPLETED: 'review.completed',
  SECURITY_SCAN_COMPLETED: 'security.completed',
  TESTS_GENERATED: 'tests.generated',
  DOCS_UPDATED: 'docs.updated',
  
  APPROVAL_REQUIRED: 'approval.required',
  APPROVAL_GRANTED: 'approval.granted',
  APPROVAL_REJECTED: 'approval.rejected',
  
  PLAN_CREATED: 'plan.created',
  PLAN_STEP_COMPLETED: 'plan.step.completed'
};
