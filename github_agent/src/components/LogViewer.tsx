import { LogEntry } from '../types';

interface LogViewerProps {
  logs: LogEntry[];
  maxHeight?: string;
}

const levelColors = {
  info: 'bg-blue-50 text-blue-700 border-blue-200',
  warning: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  error: 'bg-red-50 text-red-700 border-red-200',
  debug: 'bg-slate-50 text-slate-700 border-slate-200'
};

const levelIcons = {
  info: 'ℹ️',
  warning: '⚠️',
  error: '❌',
  debug: '🔍'
};

export default function LogViewer({ logs, maxHeight = '400px' }: LogViewerProps) {
  const formatTime = (date: Date) => {
    return new Intl.DateTimeFormat('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    }).format(date);
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-slate-900 overflow-hidden">
      <div className="bg-slate-800 border-b border-slate-700 px-4 py-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="flex gap-1.5">
            <div className="h-3 w-3 rounded-full bg-red-500"></div>
            <div className="h-3 w-3 rounded-full bg-yellow-500"></div>
            <div className="h-3 w-3 rounded-full bg-green-500"></div>
          </div>
          <span className="text-sm font-medium text-slate-300">System Logs</span>
        </div>
        <span className="text-xs text-slate-400">{logs.length} entries</span>
      </div>
      
      <div className="overflow-y-auto font-mono text-sm" style={{ maxHeight }}>
        {logs.length === 0 ? (
          <div className="p-8 text-center text-slate-500">
            No logs available
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {logs.map((log, idx) => (
              <div
                key={idx}
                className={`rounded px-3 py-2 ${
                  log.level === 'error' ? 'bg-red-950/30' :
                  log.level === 'warning' ? 'bg-yellow-950/30' :
                  log.level === 'debug' ? 'bg-slate-800/50' :
                  'bg-slate-800/30'
                }`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-slate-500 text-xs whitespace-nowrap">
                    {formatTime(log.timestamp)}
                  </span>
                  
                  <span className="text-lg">{levelIcons[log.level]}</span>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`text-xs font-medium px-2 py-0.5 rounded ${levelColors[log.level]}`}>
                        {log.level.toUpperCase()}
                      </span>
                      
                      {log.agentType && (
                        <span className="text-xs text-indigo-400 bg-indigo-950/50 px-2 py-0.5 rounded">
                          {log.agentType}
                        </span>
                      )}
                    </div>
                    
                    <p className="text-slate-300 text-sm break-words">
                      {log.message}
                    </p>
                    
                    {log.metadata && (
                      <details className="mt-1">
                        <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-400">
                          Metadata
                        </summary>
                        <pre className="mt-1 text-xs text-slate-400 bg-slate-950/50 p-2 rounded overflow-x-auto">
                          {JSON.stringify(log.metadata, null, 2)}
                        </pre>
                      </details>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
