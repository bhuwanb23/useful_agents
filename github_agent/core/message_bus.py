# core/message_bus.py
# Agents talk to each other through this
# Like a post office for agents

import asyncio
import json
import logging
from typing import Callable, Dict, List, Any
from datetime import datetime
from collections import defaultdict

class Message:
    def __init__(self, topic: str, data: Any, sender: str = "system"):
        self.id = f"{datetime.now().timestamp()}"
        self.topic = topic
        self.data = data
        self.sender = sender
        self.timestamp = datetime.now()
    
    def to_dict(self):
        return {
            "id": self.id,
            "topic": self.topic,
            "data": self.data,
            "sender": self.sender,
            "timestamp": str(self.timestamp)
        }

class MessageBus:
    """
    Pub/Sub message bus for agent communication
    
    Agents can:
    - publish messages to topics
    - subscribe to topics they care about
    - send direct messages to specific agents
    """
    
    def __init__(self):
        self.subscribers: Dict[str, List[Callable]] = defaultdict(list)
        self.message_history: List[Message] = []
        self.logger = logging.getLogger("message_bus")
        self._lock = asyncio.Lock()
    
    async def publish(self, topic: str, data: Any, sender: str = "system"):
        """Publish a message to a topic"""
        message = Message(topic, data, sender)
        
        async with self._lock:
            self.message_history.append(message)
        
        self.logger.debug(f"Published to '{topic}' from '{sender}'")
        
        # Notify all subscribers
        subscribers = self.subscribers.get(topic, [])
        
        # Also check wildcard subscribers
        for sub_topic, callbacks in self.subscribers.items():
            if sub_topic.endswith("*"):
                prefix = sub_topic[:-1]
                if topic.startswith(prefix):
                    subscribers.extend(callbacks)
        
        # Call all subscriber callbacks
        tasks = []
        for callback in subscribers:
            if asyncio.iscoroutinefunction(callback):
                tasks.append(callback(message))
            else:
                callback(message)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        return message
    
    def subscribe(self, topic: str, callback: Callable):
        """Subscribe to a topic"""
        self.subscribers[topic].append(callback)
        self.logger.debug(f"New subscriber for '{topic}'")
    
    def unsubscribe(self, topic: str, callback: Callable):
        """Unsubscribe from a topic"""
        if topic in self.subscribers:
            self.subscribers[topic].remove(callback)
    
    async def send_to_agent(self, agent_name: str, data: Any, sender: str = "system"):
        """Send direct message to specific agent"""
        topic = f"agent.{agent_name}.inbox"
        await self.publish(topic, data, sender)
    
    def get_history(self, topic_filter: str = None, limit: int = 50) -> List[Dict]:
        """Get message history"""
        history = self.message_history
        
        if topic_filter:
            history = [m for m in history if topic_filter in m.topic]
        
        return [m.to_dict() for m in history[-limit:]]
    
    def get_stats(self) -> Dict:
        """Get message bus statistics"""
        return {
            "total_messages": len(self.message_history),
            "topics": list(self.subscribers.keys()),
            "subscriber_count": sum(
                len(subs) for subs in self.subscribers.values()
            )
        }