# tests/test_core.py
"""Tests for core components: orchestrator, message_bus, task_queue, memory"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime

from core.base_agent import BaseAgent, AgentStatus, AgentPriority
from core.message_bus import MessageBus, Message
from core.task_queue import TaskQueue, Task, TaskStatus
from core.memory import SharedMemory


# ──────────────────────────────────────────────────────────────
# BASE AGENT TESTS
# ──────────────────────────────────────────────────────────────

class TestBaseAgent:
    """Test the abstract BaseAgent class."""

    def test_agent_initialization(self):
        """Test that agent initializes with correct defaults."""
        from agents.issue_analyzer import IssueAnalyzerAgent
        
        agent = IssueAnalyzerAgent()
        assert agent.name == "issue_analyzer"
        assert agent.status == AgentStatus.IDLE
        assert agent.run_count == 0
        assert agent.success_count == 0
        assert agent.failure_count == 0
        assert agent.capabilities is not None

    def test_agent_status_enum(self):
        """Test AgentStatus enum values."""
        assert AgentStatus.IDLE.value == "idle"
        assert AgentStatus.RUNNING.value == "running"
        assert AgentStatus.COMPLETED.value == "completed"
        assert AgentStatus.FAILED.value == "failed"

    def test_agent_priority_enum(self):
        """Test AgentPriority enum values."""
        assert AgentPriority.LOW.value == 1
        assert AgentPriority.NORMAL.value == 2
        assert AgentPriority.HIGH.value == 3
        assert AgentPriority.CRITICAL.value == 4

    def test_agent_stats(self):
        """Test agent statistics calculation."""
        from agents.code_fixer import CodeFixerAgent
        
        agent = CodeFixerAgent()
        agent.run_count = 10
        agent.success_count = 8
        agent.failure_count = 2
        
        stats = agent.get_stats()
        assert stats['run_count'] == 10
        assert stats['success_count'] == 8
        assert stats['failure_count'] == 2
        assert stats['success_rate'] == 80.0


# ──────────────────────────────────────────────────────────────
# MESSAGE BUS TESTS
# ──────────────────────────────────────────────────────────────

class TestMessageBus:
    """Test the pub/sub message bus."""

    @pytest.mark.asyncio
    async def test_publish_and_subscribe(self):
        """Test basic publish/subscribe functionality."""
        bus = MessageBus()
        received_messages = []
        
        def callback(msg):
            received_messages.append(msg)
        
        bus.subscribe("test.topic", callback)
        await bus.publish("test.topic", {"data": "test"}, sender="test")
        
        assert len(received_messages) == 1
        assert received_messages[0].data == {"data": "test"}

    @pytest.mark.asyncio
    async def test_wildcard_subscription(self):
        """Test wildcard topic subscriptions."""
        bus = MessageBus()
        received = []
        
        def callback(msg):
            received.append(msg)
        
        bus.subscribe("agent.*", callback)
        await bus.publish("agent.test.completed", {"status": "done"})
        
        assert len(received) == 1

    @pytest.mark.asyncio
    async def test_send_to_agent(self):
        """Test direct message sending to agents."""
        bus = MessageBus()
        received = []
        
        def callback(msg):
            received.append(msg)
        
        bus.subscribe("agent.test_agent.inbox", callback)
        await bus.send_to_agent("test_agent", {"msg": "hello"})
        
        assert len(received) == 1
        assert received[0].data == {"msg": "hello"}

    def test_message_history(self):
        """Test message history retrieval."""
        bus = MessageBus()
        
        # Can't easily test async in sync test, but verify structure
        stats = bus.get_stats()
        assert "total_messages" in stats
        assert "topics" in stats

    def test_message_to_dict(self):
        """Test message serialization."""
        msg = Message("test.topic", {"key": "value"}, "sender")
        d = msg.to_dict()
        
        assert d['topic'] == "test.topic"
        assert d['data'] == {"key": "value"}
        assert d['sender'] == "sender"
        assert 'id' in d
        assert 'timestamp' in d


# ──────────────────────────────────────────────────────────────
# TASK QUEUE TESTS
# ──────────────────────────────────────────────────────────────

class TestTaskQueue:
    """Test the priority task queue."""

    @pytest.mark.asyncio
    async def test_add_and_get_task(self):
        """Test adding and retrieving of tasks."""
        queue = TaskQueue()
        
        task = Task(type="test_task", data={"key": "value"}, priority=2)
        task_id = await queue.add_task(task)
        
        assert task_id == task.id
        retrieved = await queue.get_next_task()
        assert retrieved is not None
        assert retrieved.type == "test_task"

    @pytest.mark.asyncio
    async def test_priority_ordering(self):
        """Test that higher priority tasks are processed first."""
        queue = TaskQueue()
        
        # Add tasks in reverse priority order
        low_task = Task(type="low", data={}, priority=1)
        high_task = Task(type="high", data={}, priority=4)
        med_task = Task(type="med", data={}, priority=2)
        
        await queue.add_task(low_task)
        await queue.add_task(high_task)
        await queue.add_task(med_task)
        
        # Should get highest priority first
        first = await queue.get_next_task()
        assert first.type == "high"
        
        second = await queue.get_next_task()
        assert second.type == "med"

    @pytest.mark.asyncio
    async def test_complete_task(self):
        """Test task completion."""
        queue = TaskQueue()
        task = Task(type="test", data={})
        
        await queue.add_task(task)
        await queue.get_next_task()  # Mark as in progress
        await queue.complete_task(task.id, {"result": "success"})
        
        assert task.status == TaskStatus.COMPLETED
        assert task.result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_fail_task_with_retry(self):
        """Test task failure and retry logic."""
        queue = TaskQueue()
        task = Task(type="test", data={}, max_retries=3)
        
        await queue.add_task(task)
        await queue.get_next_task()
        
        # Fail once - should retry
        await queue.fail_task(task.id, "error 1")
        assert task.retry_count == 1
        assert task.status == TaskStatus.PENDING  # Re-queued

    @pytest.mark.asyncio
    async def test_fail_task_permanently(self):
        """Test permanent failure after max retries."""
        queue = TaskQueue()
        task = Task(type="test", data={}, max_retries=1, retry_count=1)
        
        await queue.add_task(task)
        await queue.get_next_task()
        
        # Fail again - should be permanent
        await queue.fail_task(task.id, "final error")
        assert task.status == TaskStatus.FAILED

    @pytest.mark.asyncio
    async def test_create_subtasks(self):
        """Test creating subtasks from a parent."""
        queue = TaskQueue()
        parent_task = Task(type="parent", data={})
        await queue.add_task(parent_task)
        
        subtasks = [
            {"type": "sub1", "data": {}, "priority": 2},
            {"type": "sub2", "data": {}, "priority": 3},
        ]
        
        subtask_ids = await queue.create_subtasks(parent_task.id, subtasks)
        assert len(subtask_ids) == 2

    def test_queue_stats(self):
        """Test queue statistics."""
        queue = TaskQueue()
        stats = queue.get_stats()
        
        assert "total" in stats
        assert "pending" in stats
        assert "completed" in stats
        assert "failed" in stats


# ──────────────────────────────────────────────────────────────
# SHARED MEMORY TESTS
# ──────────────────────────────────────────────────────────────

class TestSharedMemory:
    """Test the SQLite-based shared memory."""

    @pytest.fixture
    def memory(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = str(tmp_path / "test_memory.db")
        return SharedMemory(db_path=db_path)

    @pytest.mark.asyncio
    async def test_set_and_get(self, memory):
        """Test basic key-value operations."""
        await memory.set("test.key", {"value": 123}, agent="test")
        result = await memory.get("test.key")
        
        assert result == {"value": 123}

    @pytest.mark.asyncio
    async def test_get_nonexistent_key(self, memory):
        """Test getting a key that doesn't exist."""
        result = await memory.get("nonexistent.key", default="default")
        assert result == "default"

    @pytest.mark.asyncio
    async def test_delete_key(self, memory):
        """Test deleting a key."""
        await memory.set("temp.key", "value")
        await memory.delete("temp.key")
        
        result = await memory.get("temp.key")
        assert result is None

    @pytest.mark.asyncio
    async def test_track_issue(self, memory):
        """Test issue tracking."""
        await memory.track_issue(42, "owner/repo", "pending")
        
        is_processed = await memory.is_issue_processed(42)
        assert is_processed is False  # Not completed yet

    @pytest.mark.asyncio
    async def test_update_issue(self, memory):
        """Test updating issue status."""
        await memory.track_issue(42, "owner/repo", "pending")
        await memory.update_issue(42, status="completed", pr_url="http://example.com")
        
        # Get all issues and verify
        issues = await memory.get_all_issues()
        assert len(issues) == 1
        assert issues[0]['status'] == "completed"

    @pytest.mark.asyncio
    async def test_log_action(self, memory):
        """Test agent action logging."""
        await memory.log_action("test_agent", "test_action", {"data": "test"}, True)
        
        history = await memory.get_agent_history("test_agent")
        assert len(history) == 1
        assert history[0]['action'] == "test_action"

    @pytest.mark.asyncio
    async def test_get_all_agent_history(self, memory):
        """Test retrieving all agent history."""
        await memory.log_action("agent1", "action1", {}, True)
        await memory.log_action("agent2", "action2", {}, False)
        
        history = await memory.get_agent_history(limit=10)
        assert len(history) == 2
