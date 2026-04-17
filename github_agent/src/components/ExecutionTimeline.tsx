import { AgentExecution } from '../types';

interface ExecutionTimelineProps {
  execution: AgentExecution;
}

const agentColors = {
  analyzer: 'bg-purple-500',
  fixer: 'bg-blue-500',
  reviewer: 'bg-green-500',
  security: 'bg-orange-500',
  test_writer: 'bg-cyan-500',
  docs_writer: 'bg-emerald-500',
  manager: 'bg-indigo-500'
};

export default function ExecutionTimeline({ execution }: ExecutionTimelineProps) {
  const duration = execution.endTime
    ? Math.floor((execution.endTime.getTime() - execution.startTime.getTime()) / 1000)
    : Math.floor((new Date().getTime() - execution.startTime.getTime()) / 1000);

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-5">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={`h-10 w-10 rounded-lg ${agentColors[execution.agentType]} flex items-center justify-center text-white font-bold text-sm`}>
            {execution.agentType.charAt(0).toUpperCase()}
          </div>
          <div>
            <h3 className="font-semibold text-slate-900 capitalize">
              {execution.agentType.replace('_', ' ')} Agent
            </h3>
            <p className="text-sm text-slate-500">
              {execution.status === 'running' ? 'Running' : execution.status === 'completed' ? 'Completed' : 'Failed'} • {formatDuration(duration)}
            </p>
          </div>
        </div>
        
        <div className={`rounded-full px-3 py-1.5 text-sm font-medium ${
          execution.status === 'running' ? 'bg-blue-100 text-blue-700' :
          execution.status === 'completed' ? 'bg-green-100 text-green-700' :
          'bg-red-100 text-red-700'
        }`}>
          {execution.status}
        </div>
      </div>

      {/* Reasoning (if available) */}
      {execution.reasoning && (
        <div className="mb-4 rounded-lg bg-indigo-50 border border-indigo-200 p-3">
          <p className="text-xs font-medium text-indigo-900 mb-1">🧠 Agent Reasoning:</p>
          <p className="text-sm text-indigo-800">{execution.reasoning}</p>
        </div>
      )}

      {/* Timeline */}
      <div className="space-y-3">
        <p className="text-xs font-medium text-slate-700 uppercase tracking-wide">Execution Timeline</p>
        
        <div className="space-y-2 pl-4 border-l-2 border-slate-200">
          {execution.logs.map((log, idx) => {
            const timeElapsed = Math.floor((log.timestamp.getTime() - execution.startTime.getTime()) / 1000);
            
            return (
              <div key={idx} className="relative">
                {/* Timeline dot */}
                <div className={`absolute -left-[1.35rem] top-1.5 h-3 w-3 rounded-full border-2 border-white ${
                  log.level === 'error' ? 'bg-red-500' :
                  log.level === 'warning' ? 'bg-yellow-500' :
                  log.level === 'debug' ? 'bg-slate-400' :
                  'bg-blue-500'
                }`}></div>
                
                <div className="ml-2">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-mono text-slate-500">
                      +{timeElapsed}s
                    </span>
                    <span className={`text-xs font-medium px-1.5 py-0.5 rounded ${
                      log.level === 'error' ? 'bg-red-50 text-red-700' :
                      log.level === 'warning' ? 'bg-yellow-50 text-yellow-700' :
                      log.level === 'debug' ? 'bg-slate-50 text-slate-700' :
                      'bg-blue-50 text-blue-700'
                    }`}>
                      {log.level}
                    </span>
                  </div>
                  <p className="text-sm text-slate-700">{log.message}</p>
                </div>
              </div>
            );
          })}
          
          {/* Running indicator */}
          {execution.status === 'running' && (
            <div className="relative">
              <div className="absolute -left-[1.35rem] top-1.5 h-3 w-3 rounded-full border-2 border-white bg-blue-500 animate-pulse"></div>
              <div className="ml-2">
                <p className="text-sm text-slate-500 italic">Processing...</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
