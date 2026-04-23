import { Issue } from '../types';

interface IssueCardProps {
  issue: Issue;
  repositoryName?: string;
  onSelect?: (issue: Issue) => void;
}

const typeColors = {
  bug: 'bg-red-50 text-red-700 border-red-200',
  feature: 'bg-blue-50 text-blue-700 border-blue-200',
  security: 'bg-orange-50 text-orange-700 border-orange-200',
  documentation: 'bg-green-50 text-green-700 border-green-200'
};

const typeIcons = {
  bug: '🐛',
  feature: '✨',
  security: '🔒',
  documentation: '📚'
};

const statusColors = {
  pending: 'bg-slate-100 text-slate-700',
  in_progress: 'bg-blue-100 text-blue-700',
  completed: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
  awaiting_approval: 'bg-yellow-100 text-yellow-700',
  approved: 'bg-emerald-100 text-emerald-700',
  rejected: 'bg-rose-100 text-rose-700'
};

export default function IssueCard({ issue, repositoryName, onSelect }: IssueCardProps) {
  const timeAgo = (date: Date) => {
    const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000);
    
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div
      onClick={() => onSelect?.(issue)}
      className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition-all cursor-pointer hover:border-indigo-200"
    >
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <span className="text-xl flex-shrink-0">{typeIcons[issue.type]}</span>
          <div className="min-w-0 flex-1">
            <h3 className="font-semibold text-slate-900 truncate">
              #{issue.number} {issue.title}
            </h3>
            {repositoryName && (
              <p className="text-xs text-slate-500 mt-0.5">{repositoryName}</p>
            )}
          </div>
        </div>
        
        <div className={`flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium whitespace-nowrap ${statusColors[issue.status]}`}>
          {issue.status === 'in_progress' && <div className="h-1.5 w-1.5 rounded-full bg-current animate-pulse"></div>}
          {issue.status.replace('_', ' ')}
        </div>
      </div>
      
      <p className="text-sm text-slate-600 line-clamp-2 mb-3">
        {issue.description}
      </p>
      
      <div className="flex items-center justify-between text-xs">
        <span className={`inline-flex items-center gap-1 rounded border px-2 py-1 font-medium ${typeColors[issue.type]}`}>
          {issue.type}
        </span>
        
        <div className="flex items-center gap-3 text-slate-500">
          <span>Created {timeAgo(issue.createdAt)}</span>
          <span>•</span>
          <span>Updated {timeAgo(issue.updatedAt)}</span>
        </div>
      </div>
    </div>
  );
}
