# core/task_queue.py
# Manages the order of tasks across all agents

import asyncio
import heapq
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging
import uuid

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class Task:
    type: str                                      # What kind of task
    data: Dict                                     # Task data
    priority: int = 2                              # 1=low, 2=normal, 3=high, 4=critical
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_agent: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Optional[Dict] = None
    error: Optional[str] = None
    parent_task_id: Optional[str] = None          # For subtasks
    
    def __lt__(self, other):
        # Higher priority = processed first
        return self.priority > other.priority
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "data": self.data,
            "priority": self.priority,
            "status": self.status.value,
            "assigned_agent": self.assigned_agent,
            "retry_count": self.retry_count,
            "created_at": str(self.created_at),
            "error": self.error
        }

class TaskQueue:
    """
    Priority queue for managing tasks
    
    High priority tasks (bugs, security issues) go first
    Tracks task dependencies and subtasks
    """
    
    def __init__(self):
        self._queue = []
        self._tasks: Dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self.logger = logging.getLogger("task_queue")
        self._processed_count = 0
        self._failed_count = 0
    
    async def add_task(self, task: Task) -> str:
        """Add a task to the queue"""
        async with self._lock:
            heapq.heappush(self._queue, task)
            self._tasks[task.id] = task
            
        self.logger.info(
            f"Task added: {task.type} | Priority: {task.priority} | ID: {task.id[:8]}"
        )
        return task.id
    
    async def get_next_task(self) -> Optional[Task]:
        """Get the highest priority pending task"""
        async with self._lock:
            while self._queue:
                task = heapq.heappop(self._queue)
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.IN_PROGRESS
                    task.started_at = datetime.now()
                    return task
        return None
    
    async def complete_task(self, task_id: str, result: Dict):
        """Mark a task as completed"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            self._processed_count += 1
            self.logger.info(f"Task completed: {task_id[:8]}")
    
    async def fail_task(self, task_id: str, error: str):
        """Mark a task as failed, retry if possible"""
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.retry_count += 1
            
            if task.retry_count <= task.max_retries:
                # Retry the task
                task.status = TaskStatus.RETRYING
                task.error = error
                
                # Re-add to queue with delay (lower priority on retry)
                await asyncio.sleep(5 * task.retry_count)  # Back-off
                task.status = TaskStatus.PENDING
                
                async with self._lock:
                    heapq.heappush(self._queue, task)
                    
                self.logger.warning(
                    f"Task retrying ({task.retry_count}/{task.max_retries}): {task_id[:8]}"
                )
            else:
                task.status = TaskStatus.FAILED
                task.error = error
                self._failed_count += 1
                self.logger.error(f"Task permanently failed: {task_id[:8]}")
    
    async def create_subtasks(self, parent_task_id: str, subtasks: List[Dict]) -> List[str]:
        """Create multiple subtasks from a parent task"""
        task_ids = []
        for subtask_data in subtasks:
            task = Task(
                type=subtask_data['type'],
                data=subtask_data['data'],
                priority=subtask_data.get('priority', 2),
                parent_task_id=parent_task_id
            )
            task_id = await self.add_task(task)
            task_ids.append(task_id)
        return task_ids
    
    def get_stats(self) -> Dict:
        """Queue statistics"""
        all_tasks = list(self._tasks.values())
        return {
            "total": len(all_tasks),
            "pending": len([t for t in all_tasks if t.status == TaskStatus.PENDING]),
            "in_progress": len([t for t in all_tasks if t.status == TaskStatus.IN_PROGRESS]),
            "completed": self._processed_count,
            "failed": self._failed_count,
            "queue_size": len(self._queue)
        }
    
    def get_all_tasks(self) -> List[Dict]:
        return [t.to_dict() for t in self._tasks.values()]