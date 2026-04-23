// Core Type Definitions for GitHub Agent System

export type AgentType = 
  | 'analyzer'
  | 'fixer'
  | 'reviewer'
  | 'security'
  | 'test_writer'
  | 'docs_writer'
  | 'manager';

export type TaskStatus = 
  | 'pending'
  | 'in_progress'
  | 'completed'
  | 'failed'
  | 'awaiting_approval'
  | 'approved'
  | 'rejected';

export type IssueType = 'bug' | 'feature' | 'security' | 'documentation';

export interface Repository {
  id: string;
  name: string;
  owner: string;
  url: string;
  token?: string;
  isMonitoring: boolean;
  lastSync?: Date;
}

export interface Issue {
  id: string;
  repositoryId: string;
  number: number;
  title: string;
  description: string;
  type: IssueType;
  status: TaskStatus;
  createdAt: Date;
  updatedAt: Date;
}

export interface Task {
  id: string;
  issueId: string;
  agentType: AgentType;
  status: TaskStatus;
  input: any;
  output?: any;
  error?: string;
  attempts: number;
  maxAttempts: number;
  createdAt: Date;
  updatedAt: Date;
}

export interface AgentExecution {
  id: string;
  taskId: string;
  agentType: AgentType;
  status: 'running' | 'completed' | 'failed';
  startTime: Date;
  endTime?: Date;
  logs: LogEntry[];
  reasoning?: string;
  output?: any;
}

export interface LogEntry {
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
  agentType?: AgentType;
  metadata?: Record<string, any>;
}

export interface CodeChange {
  id: string;
  taskId: string;
  filePath: string;
  originalContent: string;
  modifiedContent: string;
  diff: string;
  approved: boolean;
  reviewComments?: string[];
}

export interface Plan {
  id: string;
  issueId: string;
  steps: PlanStep[];
  createdBy: 'manager';
  status: 'draft' | 'executing' | 'completed' | 'failed';
}

export interface PlanStep {
  stepNumber: number;
  description: string;
  agentType: AgentType;
  dependencies: number[];
  status: TaskStatus;
  taskId?: string;
}

export interface AgentMemory {
  taskId: string;
  agentType: AgentType;
  context: Record<string, any>;
  codeEmbeddings?: number[][];
  relatedFiles?: string[];
  timestamp: Date;
}

export interface SystemStats {
  totalRepositories: number;
  activeMonitoring: number;
  pendingIssues: number;
  inProgressTasks: number;
  completedToday: number;
  failedToday: number;
  avgResponseTime: number;
}

export interface AgentConfig {
  type: AgentType;
  name: string;
  description: string;
  capabilities: string[];
  model?: string;
  maxRetries: number;
  timeout: number;
}
