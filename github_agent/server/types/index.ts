/**
 * TypeScript type definitions for GitHub Agent System
 */

export interface AgentTask {
  taskId: string;
  repositoryId: string;
  issueId?: string;
  type: TaskType;
  input: Record<string, any>;
  priority?: number;
}

export type TaskType = 
  | 'analyze'
  | 'fix'
  | 'review'
  | 'security_scan'
  | 'test'
  | 'document';

export type TaskStatus = 
  | 'pending'
  | 'queued'
  | 'running'
  | 'completed'
  | 'failed'
  | 'retrying';

export type AgentType = 
  | 'analyzer'
  | 'fixer'
  | 'reviewer'
  | 'security'
  | 'tester'
  | 'docs'
  | 'manager';

export type IssueType = 
  | 'bug'
  | 'feature'
  | 'security'
  | 'documentation'
  | 'test';

export type IssuePriority = 'low' | 'medium' | 'high' | 'critical';

export type IssueState = 'open' | 'closed' | 'in_progress';

export interface AgentExecution {
  executionId: string;
  taskId: string;
  agentType: AgentType;
  status: 'running' | 'completed' | 'failed';
  stage?: string;
  progress: number;
  startedAt: Date;
  completedAt?: Date;
}

export interface AgentLogEntry {
  level: 'debug' | 'info' | 'warn' | 'error' | 'thought';
  message: string;
  timestamp: Date;
  metadata?: Record<string, any>;
}

export interface PromptConfig {
  systemPrompt: string;
  userPrompt: string;
  temperature: number;
  maxTokens: number;
  topP: number;
}

export interface GitHubIssue {
  id: number;
  number: number;
  title: string;
  body?: string;
  state: string;
  labels: Array<{ name: string }>;
  html_url: string;
  created_at: string;
  updated_at: string;
  closed_at?: string;
}

export interface GitHubWebhookPayload {
  action: string;
  issue?: GitHubIssue;
  repository: {
    name: string;
    owner: { login: string };
    full_name: string;
    html_url: string;
  };
}
