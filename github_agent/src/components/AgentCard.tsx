import { AgentConfig } from '../types';

interface AgentCardProps {
  config: AgentConfig;
  status: 'idle' | 'running' | 'error';
  activeTasks?: number;
  completedToday?: number;
}

const statusColors = {
  idle: 'bg-slate-100 text-slate-700',
  running: 'bg-green-100 text-green-700',
  error: 'bg-red-100 text-red-700'
};

const statusDots = {
  idle: 'bg-slate-400',
  running: 'bg-green-500 animate-pulse',
  error: 'bg-red-500 animate-pulse'
};

export default function AgentCard({ config, status, activeTasks = 0, completedToday = 0 }: AgentCardProps) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="font-semibold text-slate-900">{config.name}</h3>
          <p className="text-sm text-slate-500 mt-1">{config.description}</p>
        </div>
        
        <div className={`flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ${statusColors[status]}`}>
          <div className={`h-1.5 w-1.5 rounded-full ${statusDots[status]}`}></div>
          {status}
        </div>
      </div>
      
      <div className="space-y-2 mb-3">
        <div className="text-xs text-slate-600">
          <span className="font-medium">Model:</span> {config.model}
        </div>
        <div className="text-xs text-slate-600">
          <span className="font-medium">Max Retries:</span> {config.maxRetries} • 
          <span className="ml-1 font-medium">Timeout:</span> {config.timeout / 1000}s
        </div>
      </div>
      
      <div className="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
        <div>
          <p className="text-xs text-slate-500">Active Tasks</p>
          <p className="text-lg font-bold text-slate-900">{activeTasks}</p>
        </div>
        <div>
          <p className="text-xs text-slate-500">Completed Today</p>
          <p className="text-lg font-bold text-green-600">{completedToday}</p>
        </div>
      </div>
      
      <div className="mt-3 pt-3 border-t border-slate-100">
        <p className="text-xs font-medium text-slate-700 mb-1.5">Capabilities:</p>
        <div className="flex flex-wrap gap-1">
          {config.capabilities.slice(0, 3).map((cap, idx) => (
            <span
              key={idx}
              className="rounded bg-indigo-50 px-2 py-0.5 text-xs text-indigo-700"
            >
              {cap}
            </span>
          ))}
          {config.capabilities.length > 3 && (
            <span className="rounded bg-slate-100 px-2 py-0.5 text-xs text-slate-600">
              +{config.capabilities.length - 3} more
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
