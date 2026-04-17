import { useState } from 'react';
import Layout from './components/Layout';
import Navigation from './components/Navigation';
import StatCard from './components/StatCard';
import AgentCard from './components/AgentCard';
import IssueCard from './components/IssueCard';
import LogViewer from './components/LogViewer';
import ExecutionTimeline from './components/ExecutionTimeline';
import { AGENT_CONFIGS } from './config/agents';
import { 
  mockSystemStats, 
  mockRepositories, 
  mockIssues, 
  mockExecutions,
  mockLogs 
} from './data/mockData';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');

  return (
    <Layout>
      <Navigation activeTab={activeTab} onTabChange={setActiveTab} />

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* System Stats */}
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">System Overview</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard
                title="Active Monitoring"
                value={mockSystemStats.activeMonitoring}
                icon="👁️"
                color="green"
                trend={{ value: 12, direction: 'up' }}
              />
              <StatCard
                title="In Progress"
                value={mockSystemStats.inProgressTasks}
                icon="⚡"
                color="blue"
              />
              <StatCard
                title="Completed Today"
                value={mockSystemStats.completedToday}
                icon="✓"
                color="purple"
                trend={{ value: 25, direction: 'up' }}
              />
              <StatCard
                title="Avg Response Time"
                value={`${mockSystemStats.avgResponseTime}s`}
                icon="⏱️"
                color="yellow"
              />
            </div>
          </div>

          {/* Recent Issues */}
          <div>
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-slate-900">Recent Issues</h2>
              <button className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
                View all →
              </button>
            </div>
            <div className="grid gap-4">
              {mockIssues.slice(0, 3).map((issue) => {
                const repo = mockRepositories.find(r => r.id === issue.repositoryId);
                return (
                  <IssueCard
                    key={issue.id}
                    issue={issue}
                    repositoryName={repo ? `${repo.owner}/${repo.name}` : undefined}
                  />
                );
              })}
            </div>
          </div>

          {/* Active Executions */}
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Active Executions</h2>
            <div className="grid gap-4">
              {mockExecutions.map((execution) => (
                <ExecutionTimeline key={execution.id} execution={execution} />
              ))}
            </div>
          </div>

          {/* System Logs */}
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-4">System Logs</h2>
            <LogViewer logs={mockLogs} maxHeight="300px" />
          </div>
        </div>
      )}

      {/* Repositories Tab */}
      {activeTab === 'repositories' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Monitored Repositories</h2>
            <button className="rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
              + Add Repository
            </button>
          </div>

          <div className="grid gap-4">
            {mockRepositories.map((repo) => (
              <div
                key={repo.id}
                className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3">
                      <h3 className="text-lg font-semibold text-slate-900">
                        {repo.owner}/{repo.name}
                      </h3>
                      {repo.isMonitoring && (
                        <span className="flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700">
                          <div className="h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></div>
                          Monitoring
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-slate-500 mt-1">{repo.url}</p>
                    {repo.lastSync && (
                      <p className="text-xs text-slate-400 mt-2">
                        Last sync: {new Date(repo.lastSync).toLocaleString()}
                      </p>
                    )}
                  </div>
                  
                  <button className="text-sm font-medium text-indigo-600 hover:text-indigo-700">
                    Configure
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Issues Tab */}
      {activeTab === 'issues' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">All Issues</h2>
            <div className="flex gap-2">
              <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                <option>All Types</option>
                <option>Bug</option>
                <option>Feature</option>
                <option>Security</option>
                <option>Documentation</option>
              </select>
              <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                <option>All Status</option>
                <option>Pending</option>
                <option>In Progress</option>
                <option>Awaiting Approval</option>
                <option>Completed</option>
              </select>
            </div>
          </div>

          <div className="grid gap-4">
            {mockIssues.map((issue) => {
              const repo = mockRepositories.find(r => r.id === issue.repositoryId);
              return (
                <IssueCard
                  key={issue.id}
                  issue={issue}
                  repositoryName={repo ? `${repo.owner}/${repo.name}` : undefined}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Agents Tab */}
      {activeTab === 'agents' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Agent Fleet Status</h2>
            <p className="text-sm text-slate-600">
              Multi-agent system with specialized capabilities and autonomous operation
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Object.values(AGENT_CONFIGS).map((config) => (
              <AgentCard
                key={config.type}
                config={config}
                status={config.type === 'fixer' ? 'running' : 'idle'}
                activeTasks={config.type === 'fixer' ? 1 : 0}
                completedToday={Math.floor(Math.random() * 10)}
              />
            ))}
          </div>
        </div>
      )}

      {/* Executions Tab */}
      {activeTab === 'executions' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">Agent Executions</h2>
            <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
              <option>All Agents</option>
              <option>Analyzer</option>
              <option>Fixer</option>
              <option>Reviewer</option>
              <option>Security</option>
            </select>
          </div>

          <div className="grid gap-4">
            {mockExecutions.map((execution) => (
              <ExecutionTimeline key={execution.id} execution={execution} />
            ))}
          </div>
        </div>
      )}

      {/* Logs Tab */}
      {activeTab === 'logs' && (
        <div className="space-y-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-900">System Logs</h2>
            <div className="flex gap-2">
              <select className="rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm">
                <option>All Levels</option>
                <option>Info</option>
                <option>Warning</option>
                <option>Error</option>
                <option>Debug</option>
              </select>
              <button className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50">
                Clear
              </button>
            </div>
          </div>

          <LogViewer logs={mockLogs} maxHeight="600px" />
        </div>
      )}

      {/* Approvals Tab */}
      {activeTab === 'approvals' && (
        <div className="space-y-6">
          <div>
            <h2 className="text-lg font-semibold text-slate-900 mb-2">Pending Approvals</h2>
            <p className="text-sm text-slate-600">
              Human-in-the-Loop: Review and approve agent-generated code changes
            </p>
          </div>

          <div className="grid gap-4">
            {mockIssues
              .filter((issue) => issue.status === 'awaiting_approval')
              .map((issue) => {
                const repo = mockRepositories.find(r => r.id === issue.repositoryId);
                return (
                  <div
                    key={issue.id}
                    className="rounded-lg border-2 border-yellow-200 bg-yellow-50 p-5"
                  >
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <h3 className="font-semibold text-slate-900">
                          #{issue.number} {issue.title}
                        </h3>
                        <p className="text-sm text-slate-600 mt-1">
                          {repo ? `${repo.owner}/${repo.name}` : 'Unknown repository'}
                        </p>
                      </div>
                      <span className="rounded-full bg-yellow-100 px-3 py-1 text-sm font-medium text-yellow-700">
                        Awaiting Approval
                      </span>
                    </div>

                    <div className="rounded-lg bg-white border border-slate-200 p-4 mb-4">
                      <p className="text-sm font-medium text-slate-700 mb-2">
                        📝 Changes Summary:
                      </p>
                      <ul className="space-y-1 text-sm text-slate-600">
                        <li>• Modified: src/theme/ThemeProvider.tsx</li>
                        <li>• Modified: src/styles/global.css</li>
                        <li>• Added: src/hooks/useTheme.ts</li>
                      </ul>
                      
                      <div className="mt-3 pt-3 border-t border-slate-200">
                        <p className="text-xs font-medium text-slate-700 mb-1">
                          Code Review Score: <span className="text-green-600 font-bold">95/100</span>
                        </p>
                        <p className="text-xs text-slate-500">
                          Tests passing • No security issues • Best practices followed
                        </p>
                      </div>
                    </div>

                    <div className="flex gap-3">
                      <button className="flex-1 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-green-700">
                        ✓ Approve & Create PR
                      </button>
                      <button className="flex-1 rounded-lg border-2 border-slate-300 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 hover:bg-slate-50">
                        View Changes
                      </button>
                      <button className="rounded-lg border-2 border-red-300 bg-white px-4 py-2.5 text-sm font-medium text-red-700 hover:bg-red-50">
                        ✗ Reject
                      </button>
                    </div>
                  </div>
                );
              })}
          </div>
        </div>
      )}
    </Layout>
  );
}
