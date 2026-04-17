interface NavigationProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
}

const tabs = [
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'repositories', label: 'Repositories', icon: '📁' },
  { id: 'issues', label: 'Issues', icon: '🐛' },
  { id: 'agents', label: 'Agents', icon: '🤖' },
  { id: 'executions', label: 'Executions', icon: '⚡' },
  { id: 'logs', label: 'Logs', icon: '📝' },
  { id: 'approvals', label: 'Approvals', icon: '✓' }
];

export default function Navigation({ activeTab, onTabChange }: NavigationProps) {
  return (
    <nav className="mb-6 border-b border-slate-200 bg-white">
      <div className="flex gap-1 overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            className={`flex items-center gap-2 whitespace-nowrap border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-600 hover:border-slate-300 hover:text-slate-900'
            }`}
          >
            <span className="text-lg">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
    </nav>
  );
}
