# main.py
# Run this to start everything

import asyncio
import logging
import signal
import sys
from datetime import datetime

# Core
from core.orchestrator import Orchestrator

# All agents
from agents.issue_analyzer import IssueAnalyzerAgent
from agents.code_fixer import CodeFixerAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.security_scanner import SecurityScannerAgent
from agents.test_writer import TestWriterAgent
from agents.pr_manager import PRManagerAgent
from agents.notification_agent import NotificationAgent

# Dashboard (optional)
from dashboard.app import create_dashboard

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"logs/agent_{datetime.now().strftime('%Y%m%d')}.log")
    ]
)

def print_banner():
    print("""
╔══════════════════════════════════════════════════════════╗
║          🤖 GITHUB AGENT SYSTEM v1.0                    ║
║          Powered by Ollama + Local LLM                  ║
╚══════════════════════════════════════════════════════════╝
    """)

async def main():
    print_banner()
    
    # Initialize orchestrator
    orchestrator = Orchestrator()
    
    # Initialize and register all agents
    agents = [
        IssueAnalyzerAgent(),      # 1. Analyze issues
        CodeFixerAgent(),           # 2. Generate fixes
        CodeReviewerAgent(),        # 3. Review code
        SecurityScannerAgent(),     # 4. Security scan
        TestWriterAgent(),          # 5. Write tests
        PRManagerAgent(),           # 6. Create PRs
        NotificationAgent(),        # 7. Send notifications
    ]
    
    orchestrator.register_agents(agents)
    
    print(f"\n✅ {len(agents)} agents registered and ready")
    print("📡 Starting agent system...\n")
    
    # Handle graceful shutdown
    def shutdown(signum, frame):
        print("\n⛔ Shutdown signal received...")
        asyncio.create_task(orchestrator.stop())
        sys.exit(0)
    
    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)
    
    # Start dashboard in background thread
    import threading
    dashboard_thread = threading.Thread(
        target=lambda: create_dashboard(orchestrator).run(
            host='0.0.0.0', 
            port=5000,
            debug=False
        ),
        daemon=True
    )
    dashboard_thread.start()
    print("📊 Dashboard running at http://localhost:5000")
    
    # Start the main orchestration system
    await orchestrator.start()


if __name__ == "__main__":
    import os
    os.makedirs("logs", exist_ok=True)
    
    asyncio.run(main())