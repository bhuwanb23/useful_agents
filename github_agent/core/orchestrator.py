# core/orchestrator.py
# The BRAIN - manages all agents and coordinates work

import asyncio
import logging
from typing import Dict, List, Optional, Type
from datetime import datetime

from core.base_agent import BaseAgent, AgentStatus
from core.message_bus import MessageBus
from core.memory import SharedMemory
from core.task_queue import TaskQueue, Task
from clients.github_client import GitHubClient
from clients.ollama_client import OllamaClient

class Orchestrator:
    """
    Master orchestrator that:
    1. Manages all agents
    2. Assigns tasks to right agents
    3. Coordinates multi-step workflows
    4. Handles failures and retries
    5. Monitors everything
    """
    
    def __init__(self):
        self.logger = logging.getLogger("orchestrator")
        
        # Core systems
        self.message_bus = MessageBus()
        self.memory = SharedMemory()
        self.task_queue = TaskQueue()
        
        # Shared clients (all agents share these)
        self.github_client = GitHubClient()
        self.ollama_client = OllamaClient()
        
        # Agent registry
        self.agents: Dict[str, BaseAgent] = {}
        
        # Is the system running?
        self.running = False
        
        # Stats
        self.start_time = None
        self.total_issues_processed = 0
        self.total_prs_created = 0
        
        self.logger.info("🎯 Orchestrator initialized")
    
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        # Give agent access to shared resources
        agent.memory = self.memory
        agent.message_bus = self.message_bus
        agent.ollama = self.ollama_client
        agent.github = self.github_client
        
        # Register in agent registry
        self.agents[agent.name] = agent
        
        # Subscribe to agent's inbox
        self.message_bus.subscribe(
            f"agent.{agent.name}.inbox",
            lambda msg: asyncio.create_task(
                self._route_to_agent(agent.name, msg.data)
            )
        )
        
        self.logger.info(f"✅ Agent registered: {agent.name}")
    
    def register_agents(self, agents: List[BaseAgent]):
        """Register multiple agents at once"""
        for agent in agents:
            self.register_agent(agent)
    
    async def start(self):
        """Start the orchestration system"""
        self.running = True
        self.start_time = datetime.now()
        
        self.logger.info("🚀 Starting orchestration system")
        self.logger.info(f"📦 Registered agents: {list(self.agents.keys())}")
        
        # Setup message bus subscriptions
        self._setup_subscriptions()
        
        # Start the main loop
        await asyncio.gather(
            self._issue_fetcher_loop(),     # Continuously fetch new issues
            self._task_processor_loop(),    # Process tasks from queue
            self._health_monitor_loop(),    # Monitor agent health
            self._cleanup_loop(),           # Cleanup old data
        )
    
    def _setup_subscriptions(self):
        """Setup message bus event handlers"""
        
        # When issue analyzer completes
        self.message_bus.subscribe(
            "agent.issue_analyzer.completed",
            self._on_analysis_complete
        )
        
        # When code fixer completes
        self.message_bus.subscribe(
            "agent.code_fixer.completed",
            self._on_fix_complete
        )
        
        # When reviewer approves
        self.message_bus.subscribe(
            "agent.code_reviewer.completed",
            self._on_review_complete
        )
        
        # When security scan completes
        self.message_bus.subscribe(
            "agent.security_scanner.completed",
            self._on_security_complete
        )
        
        # When test writer completes
        self.message_bus.subscribe(
            "agent.test_writer.completed",
            self._on_tests_complete
        )
        
        # When PR is created
        self.message_bus.subscribe(
            "agent.pr_manager.completed",
            self._on_pr_created
        )
    
    # ──────────────────────────────────────
    # MAIN LOOPS
    # ──────────────────────────────────────
    
    async def _issue_fetcher_loop(self):
        """Continuously fetch new GitHub issues"""
        from config.settings import Config
        
        while self.running:
            try:
                self.logger.info("🔍 Fetching new issues...")
                
                # Fetch issues from GitHub
                issues = self.github_client.get_open_issues(
                    labels=Config.ISSUE_LABELS,
                    limit=Config.MAX_ISSUES
                )
                
                for issue in issues:
                    # Skip already processed issues
                    if await self.memory.is_issue_processed(issue['number']):
                        continue
                    
                    # Track this issue
                    await self.memory.track_issue(
                        issue['number'],
                        Config.GITHUB_REPO,
                        "pending"
                    )
                    
                    # Create analysis task
                    task = Task(
                        type="analyze_issue",
                        data={"issue": issue},
                        priority=self._get_issue_priority(issue)
                    )
                    
                    await self.task_queue.add_task(task)
                    self.logger.info(f"📋 Queued issue #{issue['number']}: {issue['title']}")
                
            except Exception as e:
                self.logger.error(f"Issue fetcher error: {e}")
            
            # Wait before fetching again (5 minutes)
            await asyncio.sleep(300)
    
    async def _task_processor_loop(self):
        """Process tasks from the queue"""
        while self.running:
            task = await self.task_queue.get_next_task()
            
            if task:
                # Run task in background (don't block the loop)
                asyncio.create_task(self._process_task(task))
            else:
                # No tasks, wait a bit
                await asyncio.sleep(1)
    
    async def _health_monitor_loop(self):
        """Monitor agent health and restart if needed"""
        while self.running:
            for agent_name, agent in self.agents.items():
                stats = agent.get_stats()
                
                # Alert if failure rate is high
                if stats['run_count'] > 5 and stats['success_rate'] < 50:
                    self.logger.warning(
                        f"⚠️ Agent '{agent_name}' has low success rate: {stats['success_rate']:.1f}%"
                    )
                
                # Log stats to memory
                await self.memory.set(
                    f"agent.{agent_name}.stats",
                    stats,
                    "orchestrator"
                )
            
            await asyncio.sleep(60)  # Check every minute
    
    async def _cleanup_loop(self):
        """Cleanup old data"""
        while self.running:
            # Clean up expired memory keys
            # Clean up old task results
            await asyncio.sleep(3600)  # Every hour
    
    # ──────────────────────────────────────
    # TASK PROCESSING
    # ──────────────────────────────────────
    
    async def _process_task(self, task: Task):
        """Route a task to the right agent"""
        try:
            # Find the right agent for this task
            agent = self._find_agent_for_task(task)
            
            if not agent:
                self.logger.warning(f"No agent found for task type: {task.type}")
                await self.task_queue.fail_task(task.id, "No agent available")
                return
            
            task.assigned_agent = agent.name
            self.logger.info(f"📨 Routing task '{task.type}' to agent '{agent.name}'")
            
            # Execute the task
            result = await agent.run(task.data)
            
            if result['success']:
                await self.task_queue.complete_task(task.id, result)
                await self.memory.log_action(
                    agent.name, task.type, task.data, True
                )
            else:
                await self.task_queue.fail_task(task.id, result.get('error', 'Unknown error'))
                await self.memory.log_action(
                    agent.name, task.type, task.data, False
                )
                
        except Exception as e:
            self.logger.error(f"Task processing error: {e}")
            await self.task_queue.fail_task(task.id, str(e))
    
    def _find_agent_for_task(self, task: Task) -> Optional[BaseAgent]:
        """Find the best agent for a task"""
        task_agent_map = {
            "analyze_issue": "issue_analyzer",
            "fix_code": "code_fixer",
            "write_tests": "test_writer",
            "review_code": "code_reviewer",
            "scan_security": "security_scanner",
            "write_docs": "docs_writer",
            "create_pr": "pr_manager",
            "check_deps": "dependency_agent",
            "notify": "notification_agent"
        }
        
        agent_name = task_agent_map.get(task.type)
        
        if agent_name and agent_name in self.agents:
            agent = self.agents[agent_name]
            if agent.status != AgentStatus.RUNNING:
                return agent
        
        return None
    
    def _get_issue_priority(self, issue: Dict) -> int:
        """Determine task priority from issue"""
        labels = [l.lower() for l in issue.get('labels', [])]
        title = issue.get('title', '').lower()
        
        if 'critical' in labels or 'security' in labels:
            return 4
        elif 'bug' in labels or 'crash' in title:
            return 3
        elif 'enhancement' in labels or 'feature' in labels:
            return 2
        else:
            return 1
    
    # ──────────────────────────────────────
    # WORKFLOW EVENT HANDLERS
    # ──────────────────────────────────────
    
    async def _on_analysis_complete(self, message):
        """When issue analysis is done, create fix task"""
        result = message.data.get('result', {})
        analysis = result.get('analysis', {})
        issue = result.get('issue', {})
        
        if not analysis.get('can_autofix'):
            self.logger.info(f"Issue #{issue.get('number')} skipped - too complex")
            await self.memory.update_issue(issue['number'], status='skipped')
            return
        
        # Create the next tasks in the pipeline
        subtasks = [
            {
                "type": "fix_code",
                "data": {"issue": issue, "analysis": analysis},
                "priority": 3
            },
            {
                "type": "scan_security",
                "data": {"issue": issue},
                "priority": 4
            }
        ]
        
        await self.task_queue.create_subtasks(
            message.data.get('task_id', ''),
            subtasks
        )
    
    async def _on_fix_complete(self, message):
        """When code fix is done, create review task"""
        result = message.data.get('result', {})
        
        if not result.get('fixes'):
            return
        
        # Queue code review
        task = Task(
            type="review_code",
            data={
                "issue": result.get('issue'),
                "fixes": result.get('fixes'),
                "analysis": result.get('analysis')
            },
            priority=3
        )
        await self.task_queue.add_task(task)
    
    async def _on_review_complete(self, message):
        """When review is done, create PR"""
        result = message.data.get('result', {})
        
        if not result.get('approved'):
            self.logger.info("Code review rejected, not creating PR")
            return
        
        # Queue test writing and PR creation
        task = Task(
            type="write_tests",
            data={
                "issue": result.get('issue'),
                "fixes": result.get('fixes')
            },
            priority=2
        )
        await self.task_queue.add_task(task)
    
    async def _on_security_complete(self, message):
        """Handle security scan results"""
        result = message.data.get('result', {})
        
        if result.get('has_vulnerabilities'):
            self.logger.warning("🔒 Security issues found - blocking PR creation")
            issue_number = result.get('issue', {}).get('number')
            await self.memory.update_issue(
                issue_number,
                status='security_blocked'
            )
    
    async def _on_tests_complete(self, message):
        """When tests are written, create PR"""
        result = message.data.get('result', {})
        
        task = Task(
            type="create_pr",
            data={
                "issue": result.get('issue'),
                "fixes": result.get('fixes'),
                "tests": result.get('tests'),
                "analysis": result.get('analysis')
            },
            priority=3
        )
        await self.task_queue.add_task(task)
    
    async def _on_pr_created(self, message):
        """When PR is created, notify and update tracking"""
        result = message.data.get('result', {})
        issue = result.get('issue', {})
        pr = result.get('pr')
        
        if pr:
            self.total_prs_created += 1
            self.total_issues_processed += 1
            
            await self.memory.update_issue(
                issue.get('number'),
                status='completed',
                pr_url=pr.get('url')
            )
            
            # Queue notification
            task = Task(
                type="notify",
                data={
                    "type": "pr_created",
                    "issue": issue,
                    "pr_url": pr.get('url')
                },
                priority=1
            )
            await self.task_queue.add_task(task)
    
    async def _route_to_agent(self, agent_name: str, data: Dict):
        """Route direct messages to agents"""
        if agent_name in self.agents:
            await self.agents[agent_name].run(data)
    
    # ──────────────────────────────────────
    # MONITORING & STATS
    # ──────────────────────────────────────
    
    def get_system_stats(self) -> Dict:
        """Get complete system statistics"""
        uptime = (datetime.now() - self.start_time).seconds if self.start_time else 0
        
        return {
            "uptime_seconds": uptime,
            "total_issues_processed": self.total_issues_processed,
            "total_prs_created": self.total_prs_created,
            "queue_stats": self.task_queue.get_stats(),
            "message_bus_stats": self.message_bus.get_stats(),
            "agents": {
                name: agent.get_stats() 
                for name, agent in self.agents.items()
            }
        }
    
    async def stop(self):
        """Gracefully stop the system"""
        self.logger.info("🛑 Stopping orchestration system...")
        self.running = False
        
        # Wait for running agents to finish
        for agent in self.agents.values():
            while agent.status == AgentStatus.RUNNING:
                await asyncio.sleep(0.5)
        
        self.logger.info("✅ System stopped gracefully")