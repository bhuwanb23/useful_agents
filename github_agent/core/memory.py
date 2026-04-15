# core/memory.py
# Shared state between all agents
# Agents store and read information here

import json
import asyncio
import sqlite3
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

class SharedMemory:
    """
    Shared memory for all agents
    Persisted to SQLite so nothing is lost on restart
    
    Think of it like a shared notebook all agents can read/write
    """
    
    def __init__(self, db_path: str = "agent_memory.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("memory")
        self._lock = asyncio.Lock()
        self._setup_db()
    
    def _setup_db(self):
        """Create database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Key-value store for general data
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memory (
                key TEXT PRIMARY KEY,
                value TEXT,
                agent TEXT,
                updated_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        # Issue tracking - which issues are being processed
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS issue_tracker (
                issue_number INTEGER PRIMARY KEY,
                repo TEXT,
                status TEXT,
                assigned_agent TEXT,
                analysis TEXT,
                fixes TEXT,
                pr_url TEXT,
                created_at TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        
        # Agent logs - what each agent has done
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_actions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent TEXT,
                action TEXT,
                data TEXT,
                success BOOLEAN,
                timestamp TIMESTAMP
            )
        """)
        
        # PR tracking
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS pr_tracker (
                pr_number INTEGER,
                repo TEXT,
                issue_number INTEGER,
                status TEXT,
                created_at TIMESTAMP,
                merged_at TIMESTAMP,
                PRIMARY KEY (pr_number, repo)
            )
        """)
        
        conn.commit()
        conn.close()
        self.logger.info("Database initialized")
    
    # ──────────────────────────────────────
    # KEY-VALUE OPERATIONS
    # ──────────────────────────────────────
    
    async def set(self, key: str, value: Any, agent: str = "system", ttl: int = None):
        """Store a value in memory"""
        async with self._lock:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            expires_at = None
            if ttl:
                from datetime import timedelta
                expires_at = datetime.now() + timedelta(seconds=ttl)
            
            cursor.execute("""
                INSERT OR REPLACE INTO memory 
                (key, value, agent, updated_at, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (key, json.dumps(value), agent, datetime.now(), expires_at))
            
            conn.commit()
            conn.close()
    
    async def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT value, expires_at FROM memory 
            WHERE key = ?
        """, (key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return default
        
        # Check if expired
        if row[1]:
            expires_at = datetime.fromisoformat(row[1])
            if datetime.now() > expires_at:
                await self.delete(key)
                return default
        
        return json.loads(row[0])
    
    async def delete(self, key: str):
        """Delete a key from memory"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM memory WHERE key = ?", (key,))
        conn.commit()
        conn.close()
    
    # ──────────────────────────────────────
    # ISSUE TRACKING
    # ──────────────────────────────────────
    
    async def track_issue(self, issue_number: int, repo: str, status: str = "pending"):
        """Start tracking an issue"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO issue_tracker
            (issue_number, repo, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (issue_number, repo, status, datetime.now(), datetime.now()))
        
        conn.commit()
        conn.close()
    
    async def update_issue(self, issue_number: int, **kwargs):
        """Update issue tracking info"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build dynamic update query
        updates = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now(), issue_number]
        
        cursor.execute(f"""
            UPDATE issue_tracker 
            SET {updates}, updated_at = ?
            WHERE issue_number = ?
        """, values)
        
        conn.commit()
        conn.close()
    
    async def is_issue_processed(self, issue_number: int) -> bool:
        """Check if an issue was already handled"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT status FROM issue_tracker 
            WHERE issue_number = ? AND status IN ('completed', 'skipped')
        """, (issue_number,))
        
        result = cursor.fetchone()
        conn.close()
        return result is not None
    
    async def get_all_issues(self) -> List[Dict]:
        """Get all tracked issues"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM issue_tracker ORDER BY updated_at DESC")
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]
    
    # ──────────────────────────────────────
    # AGENT ACTION LOGGING
    # ──────────────────────────────────────
    
    async def log_action(self, agent: str, action: str, data: Any, success: bool):
        """Log what an agent did"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_actions (agent, action, data, success, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (agent, action, json.dumps(data), success, datetime.now()))
        
        conn.commit()
        conn.close()
    
    async def get_agent_history(self, agent: str = None, limit: int = 100) -> List[Dict]:
        """Get agent action history"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if agent:
            cursor.execute("""
                SELECT * FROM agent_actions 
                WHERE agent = ? 
                ORDER BY timestamp DESC LIMIT ?
            """, (agent, limit))
        else:
            cursor.execute("""
                SELECT * FROM agent_actions 
                ORDER BY timestamp DESC LIMIT ?
            """, (limit,))
        
        rows = cursor.fetchall()
        columns = [d[0] for d in cursor.description]
        conn.close()
        
        return [dict(zip(columns, row)) for row in rows]