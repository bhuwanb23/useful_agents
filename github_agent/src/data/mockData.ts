import { Repository, Issue, Task, AgentExecution, SystemStats, LogEntry } from '../types';

// Mock data for development and UI demonstration

export const mockRepositories: Repository[] = [
  {
    id: 'repo-1',
    name: 'web-app',
    owner: 'acme-corp',
    url: 'https://github.com/acme-corp/web-app',
    isMonitoring: true,
    lastSync: new Date(Date.now() - 300000)
  },
  {
    id: 'repo-2',
    name: 'api-service',
    owner: 'acme-corp',
    url: 'https://github.com/acme-corp/api-service',
    isMonitoring: true,
    lastSync: new Date(Date.now() - 600000)
  },
  {
    id: 'repo-3',
    name: 'mobile-app',
    owner: 'acme-corp',
    url: 'https://github.com/acme-corp/mobile-app',
    isMonitoring: false,
    lastSync: new Date(Date.now() - 86400000)
  }
];

export const mockIssues: Issue[] = [
  {
    id: 'issue-1',
    repositoryId: 'repo-1',
    number: 142,
    title: 'Authentication fails with OAuth2 tokens',
    description: 'Users cannot login using Google OAuth. Error 401 returned.',
    type: 'bug',
    status: 'in_progress',
    createdAt: new Date(Date.now() - 7200000),
    updatedAt: new Date(Date.now() - 600000)
  },
  {
    id: 'issue-2',
    repositoryId: 'repo-1',
    number: 143,
    title: 'Add dark mode support',
    description: 'Implement dark mode toggle with theme persistence',
    type: 'feature',
    status: 'awaiting_approval',
    createdAt: new Date(Date.now() - 3600000),
    updatedAt: new Date(Date.now() - 300000)
  },
  {
    id: 'issue-3',
    repositoryId: 'repo-2',
    number: 89,
    title: 'SQL injection vulnerability in search endpoint',
    description: 'Discovered potential SQL injection in /api/search',
    type: 'security',
    status: 'pending',
    createdAt: new Date(Date.now() - 1800000),
    updatedAt: new Date(Date.now() - 1800000)
  }
];

export const mockTasks: Task[] = [
  {
    id: 'task-1',
    issueId: 'issue-1',
    agentType: 'analyzer',
    status: 'completed',
    input: { issueNumber: 142 },
    output: { classification: 'bug', severity: 'high', relatedIssues: [138, 140] },
    attempts: 1,
    maxAttempts: 3,
    createdAt: new Date(Date.now() - 7200000),
    updatedAt: new Date(Date.now() - 7000000)
  },
  {
    id: 'task-2',
    issueId: 'issue-1',
    agentType: 'fixer',
    status: 'in_progress',
    input: { files: ['src/auth/oauth.ts', 'src/middleware/auth.ts'] },
    attempts: 2,
    maxAttempts: 3,
    createdAt: new Date(Date.now() - 3600000),
    updatedAt: new Date(Date.now() - 600000)
  },
  {
    id: 'task-3',
    issueId: 'issue-2',
    agentType: 'fixer',
    status: 'completed',
    input: { feature: 'dark-mode' },
    output: { filesChanged: ['src/theme/ThemeProvider.tsx', 'src/styles/global.css'] },
    attempts: 1,
    maxAttempts: 3,
    createdAt: new Date(Date.now() - 1800000),
    updatedAt: new Date(Date.now() - 900000)
  },
  {
    id: 'task-4',
    issueId: 'issue-2',
    agentType: 'reviewer',
    status: 'completed',
    input: { taskId: 'task-3' },
    output: { approved: true, score: 95 },
    attempts: 1,
    maxAttempts: 3,
    createdAt: new Date(Date.now() - 900000),
    updatedAt: new Date(Date.now() - 300000)
  }
];

export const mockExecutions: AgentExecution[] = [
  {
    id: 'exec-1',
    taskId: 'task-2',
    agentType: 'fixer',
    status: 'running',
    startTime: new Date(Date.now() - 600000),
    logs: [
      {
        timestamp: new Date(Date.now() - 600000),
        level: 'info',
        message: 'Starting code analysis for OAuth authentication issue',
        agentType: 'fixer'
      },
      {
        timestamp: new Date(Date.now() - 580000),
        level: 'info',
        message: 'Retrieved code embeddings from vector database',
        agentType: 'fixer'
      },
      {
        timestamp: new Date(Date.now() - 560000),
        level: 'debug',
        message: 'Found 3 related authentication modules',
        agentType: 'fixer'
      },
      {
        timestamp: new Date(Date.now() - 540000),
        level: 'info',
        message: 'Generating fix for oauth.ts',
        agentType: 'fixer'
      },
      {
        timestamp: new Date(Date.now() - 300000),
        level: 'warning',
        message: 'First attempt failed validation, retrying with improved context',
        agentType: 'fixer'
      },
      {
        timestamp: new Date(Date.now() - 120000),
        level: 'info',
        message: 'Applying fixes to 2 files',
        agentType: 'fixer'
      }
    ],
    reasoning: 'The OAuth token validation was failing because the token expiry check was using server time instead of UTC. Fixed by normalizing all timestamps to UTC and adding proper token refresh logic.'
  }
];

export const mockLogs: LogEntry[] = [
  {
    timestamp: new Date(Date.now() - 600000),
    level: 'info',
    message: 'Orchestrator started monitoring repository: acme-corp/web-app',
    metadata: { repositoryId: 'repo-1' }
  },
  {
    timestamp: new Date(Date.now() - 580000),
    level: 'info',
    message: 'New issue detected: #142 - Authentication fails with OAuth2 tokens',
    agentType: 'analyzer',
    metadata: { issueId: 'issue-1' }
  },
  {
    timestamp: new Date(Date.now() - 560000),
    level: 'info',
    message: 'Task dispatched to Analyzer Agent',
    agentType: 'analyzer',
    metadata: { taskId: 'task-1' }
  },
  {
    timestamp: new Date(Date.now() - 540000),
    level: 'info',
    message: 'Issue classified as: HIGH severity BUG',
    agentType: 'analyzer'
  },
  {
    timestamp: new Date(Date.now() - 520000),
    level: 'info',
    message: 'Task dispatched to Code Fixer Agent',
    agentType: 'fixer',
    metadata: { taskId: 'task-2' }
  },
  {
    timestamp: new Date(Date.now() - 300000),
    level: 'warning',
    message: 'Code fix attempt 1 rejected by reviewer',
    agentType: 'fixer'
  },
  {
    timestamp: new Date(Date.now() - 280000),
    level: 'info',
    message: 'Initiating self-correction loop',
    agentType: 'fixer'
  },
  {
    timestamp: new Date(Date.now() - 120000),
    level: 'info',
    message: 'Code fix attempt 2 in progress',
    agentType: 'fixer'
  }
];

export const mockSystemStats: SystemStats = {
  totalRepositories: 3,
  activeMonitoring: 2,
  pendingIssues: 1,
  inProgressTasks: 1,
  completedToday: 8,
  failedToday: 2,
  avgResponseTime: 245 // seconds
};
