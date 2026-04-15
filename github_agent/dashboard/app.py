# dashboard/app.py
# See everything happening in real-time

from flask import Flask, render_template_string, jsonify
from datetime import datetime

def create_dashboard(orchestrator):
    app = Flask(__name__)
    
    DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>🤖 GitHub Agent Dashboard</title>
    <meta http-equiv="refresh" content="10">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', sans-serif; 
            background: #0d1117; 
            color: #c9d1d9; 
            padding: 20px;
        }
        h1 { color: #58a6ff; margin-bottom: 20px; font-size: 24px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { 
            background: #161b22; 
            border: 1px solid #30363d; 
            border-radius: 8px; 
            padding: 20px;
        }
        .card h2 { color: #58a6ff; margin-bottom: 15px; font-size: 16px; }
        .stat { 
            display: flex; 
            justify-content: space-between; 
            padding: 8px 0; 
            border-bottom: 1px solid #21262d;
        }
        .stat-value { color: #3fb950; font-weight: bold; }
        .agent-status { 
            display: inline-block; 
            padding: 2px 8px; 
            border-radius: 12px; 
            font-size: 12px;
        }
        .status-idle { background: #1f6feb33; color: #58a6ff; }
        .status-running { background: #3fb95033; color: #3fb950; }
        .status-failed { background: #da363433; color: #f85149; }
        .issue-row { padding: 10px 0; border-bottom: 1px solid #21262d; }
        .badge { 
            display: inline-block; padding: 2px 8px; 
            border-radius: 12px; font-size: 11px; margin-left: 8px;
        }
        .badge-success { background: #3fb95033; color: #3fb950; }
        .badge-pending { background: #d2992233; color: #d29922; }
        .badge-failed { background: #da363433; color: #f85149; }
        .refresh-note { 
            color: #8b949e; font-size: 12px; 
            text-align: right; margin-bottom: 10px; 
        }
    </style>
</head>
<body>
    <h1>🤖 GitHub Agent System Dashboard</h1>
    <p class="refresh-note">Auto-refreshes every 10 seconds | {{ time }}</p>
    
    <div class="grid">
        <!-- System Stats -->
        <div class="card">
            <h2>📊 System Overview</h2>
            <div class="stat">
                <span>Total Issues Processed</span>
                <span class="stat-value">{{ stats.total_issues_processed }}</span>
            </div>
            <div class="stat">
                <span>PRs Created</span>
                <span class="stat-value">{{ stats.total_prs_created }}</span>
            </div>
            <div class="stat">
                <span>Tasks in Queue</span>
                <span class="stat-value">{{ stats.queue_stats.pending }}</span>
            </div>
            <div class="stat">
                <span>Tasks Running</span>
                <span class="stat-value">{{ stats.queue_stats.in_progress }}</span>
            </div>
            <div class="stat">
                <span>Uptime</span>
                <span class="stat-value">{{ stats.uptime_seconds }}s</span>
            </div>
        </div>
        
        <!-- Agent Status -->
        <div class="card">
            <h2>🤖 Agent Status</h2>
            {% for name, agent in stats.agents.items() %}
            <div class="stat">
                <span>{{ name }}</span>
                <span>
                    <span class="agent-status status-{{ agent.status }}">{{ agent.status }}</span>
                    <small style="color: #8b949e;"> {{ agent.success_rate|round(0) }}%</small>
                </span>
            </div>
            {% endfor %}
        </div>
        
        <!-- Recent Issues -->
        <div class="card">
            <h2>📋 Recent Issues</h2>
            {% for issue in issues[:10] %}
            <div class="issue-row">
                <span>#{{ issue.issue_number }}</span>
                <span class="badge badge-{{ issue.status }}">{{ issue.status }}</span>
                {% if issue.pr_url %}
                <a href="{{ issue.pr_url }}" style="color: #58a6ff; font-size: 12px;"> → PR</a>
                {% endif %}
            </div>
            {% endfor %}
        </div>
        
        <!-- Queue Stats -->
        <div class="card">
            <h2>⚙️ Task Queue</h2>
            <div class="stat">
                <span>Pending</span>
                <span class="stat-value">{{ stats.queue_stats.pending }}</span>
            </div>
            <div class="stat">
                <span>Completed</span>
                <span class="stat-value">{{ stats.queue_stats.completed }}</span>
            </div>
            <div class="stat">
                <span>Failed</span>
                <span class="stat-value" style="color: #f85149;">{{ stats.queue_stats.failed }}</span>
            </div>
        </div>
    </div>
</body>
</html>
    """
    
    @app.route('/')
    def dashboard():
        stats = orchestrator.get_system_stats()
        issues = []
        
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            issues = loop.run_until_complete(
                orchestrator.memory.get_all_issues()
            )
            loop.close()
        except:
            pass
        
        return render_template_string(
            DASHBOARD_HTML,
            stats=stats,
            issues=issues,
            time=datetime.now().strftime('%H:%M:%S')
        )
    
    @app.route('/api/stats')
    def api_stats():
        return jsonify(orchestrator.get_system_stats())
    
    @app.route('/api/issues')
    def api_issues():
        import asyncio
        loop = asyncio.new_event_loop()
        issues = loop.run_until_complete(orchestrator.memory.get_all_issues())
        loop.close()
        return jsonify(issues)
    
    return app