# core/base_agent.py
# Every agent inherits from this - gives them all same powers

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum

class AgentStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class AgentPriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class BaseAgent(ABC):
    """
    Base class for all agents in the system
    Every agent must inherit this and implement 'execute'
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_run = None
        self.run_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.logger = logging.getLogger(f"agent.{name}")
        
        # Will be set by orchestrator
        self.memory = None
        self.message_bus = None
        self.ollama = None
        self.github = None
        
        # Agent capabilities - what it can do
        self.capabilities = []
        
        self.logger.info(f"Agent '{name}' initialized")
    
    @abstractmethod
    async def execute(self, task: Dict) -> Dict:
        """
        Main execution method - every agent MUST implement this
        
        Args:
            task: Dict with task details
            
        Returns:
            Dict with results
        """
        pass
    
    @abstractmethod
    def can_handle(self, task: Dict) -> bool:
        """
        Check if this agent can handle a given task
        """
        pass
    
    async def run(self, task: Dict) -> Dict:
        """Wrapper around execute with error handling"""
        self.status = AgentStatus.RUNNING
        self.last_run = datetime.now()
        self.run_count += 1
        
        self.logger.info(f"Starting task: {task.get('type', 'unknown')}")
        
        try:
            # Pre-execution hooks
            await self._before_execute(task)
            
            # Run the actual agent logic
            result = await self.execute(task)
            
            # Post-execution hooks
            await self._after_execute(task, result)
            
            self.status = AgentStatus.COMPLETED
            self.success_count += 1
            
            # Announce completion to message bus
            if self.message_bus:
                await self.message_bus.publish(
                    f"agent.{self.name}.completed",
                    {
                        "agent": self.name,
                        "task": task,
                        "result": result
                    }
                )
            
            return {"success": True, "result": result, "agent": self.name}
            
        except Exception as e:
            self.status = AgentStatus.FAILED
            self.failure_count += 1
            self.logger.error(f"Agent failed: {str(e)}", exc_info=True)
            
            # Announce failure
            if self.message_bus:
                await self.message_bus.publish(
                    f"agent.{self.name}.failed",
                    {"agent": self.name, "task": task, "error": str(e)}
                )
            
            return {"success": False, "error": str(e), "agent": self.name}
    
    async def _before_execute(self, task: Dict):
        """Hook called before execution"""
        self.logger.debug(f"Before execute: {task}")
    
    async def _after_execute(self, task: Dict, result: Dict):
        """Hook called after execution"""
        self.logger.debug(f"After execute, result keys: {result.keys()}")
    
    def get_stats(self) -> Dict:
        """Return agent statistics"""
        return {
            "name": self.name,
            "status": self.status.value,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": (
                self.success_count / self.run_count * 100 
                if self.run_count > 0 else 0
            ),
            "last_run": str(self.last_run),
            "capabilities": self.capabilities
        }
    
    def __repr__(self):
        return f"<Agent: {self.name} | Status: {self.status.value}>"