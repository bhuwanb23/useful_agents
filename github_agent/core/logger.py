# core/logger.py
# Centralized logging for the entire system
# Every agent and component uses this

import logging
import logging.handlers
import os
import json
from datetime import datetime
from typing import Optional
from pathlib import Path
from colorlog import ColoredFormatter


# ──────────────────────────────────────────────────────────────
# COLOR SCHEME FOR TERMINAL OUTPUT
# ──────────────────────────────────────────────────────────────

LOG_COLORS = {
    'DEBUG':    'cyan',
    'INFO':     'green',
    'WARNING':  'yellow',
    'ERROR':    'red',
    'CRITICAL': 'red,bg_white',
}

AGENT_COLORS = {
    'orchestrator':       'blue',
    'issue_analyzer':     'cyan',
    'code_fixer':         'green',
    'code_reviewer':      'yellow',
    'security_scanner':   'red',
    'test_writer':        'magenta',
    'pr_manager':         'blue',
    'notification_agent': 'white',
    'dependency_agent':   'cyan',
    'docs_writer':        'green',
}


# ──────────────────────────────────────────────────────────────
# JSON LOG FORMATTER
# Writes structured logs for analysis/monitoring
# ──────────────────────────────────────────────────────────────

class JSONFormatter(logging.Formatter):
    """
    Formats logs as JSON for easy parsing
    Used for file logging and monitoring tools
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level":     record.levelname,
            "logger":    record.name,
            "message":   record.getMessage(),
            "module":    record.module,
            "line":      record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields attached to the record
        extras = {
            k: v for k, v in record.__dict__.items()
            if k not in {
                'name', 'msg', 'args', 'levelname', 'levelno',
                'pathname', 'filename', 'module', 'exc_info',
                'exc_text', 'stack_info', 'lineno', 'funcName',
                'created', 'msecs', 'relativeCreated', 'thread',
                'threadName', 'processName', 'process', 'message'
            }
        }
        if extras:
            log_data["extra"] = extras

        return json.dumps(log_data)


# ──────────────────────────────────────────────────────────────
# AGENT-SPECIFIC LOGGER
# ──────────────────────────────────────────────────────────────

class AgentLogger:
    """
    Custom logger wrapper for agents
    Adds agent context to every log message
    Also tracks log stats (errors, warnings, etc.)
    """

    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self._logger = logging.getLogger(f"agent.{agent_name}")
        self.error_count   = 0
        self.warning_count = 0
        self.info_count    = 0

    def info(self, msg: str, **kwargs):
        self.info_count += 1
        self._logger.info(f"[{self.agent_name}] {msg}", extra=kwargs)

    def warning(self, msg: str, **kwargs):
        self.warning_count += 1
        self._logger.warning(f"[{self.agent_name}] ⚠️  {msg}", extra=kwargs)

    def error(self, msg: str, **kwargs):
        self.error_count += 1
        self._logger.error(f"[{self.agent_name}] ❌ {msg}", extra=kwargs)

    def debug(self, msg: str, **kwargs):
        self._logger.debug(f"[{self.agent_name}] {msg}", extra=kwargs)

    def critical(self, msg: str, **kwargs):
        self.error_count += 1
        self._logger.critical(f"[{self.agent_name}] 🚨 {msg}", extra=kwargs)

    def success(self, msg: str, **kwargs):
        """Custom SUCCESS level (logged as INFO with prefix)"""
        self._logger.info(f"[{self.agent_name}] ✅ {msg}", extra=kwargs)

    def task_start(self, task_type: str, task_id: str):
        self._logger.info(
            f"[{self.agent_name}] 🚀 Starting task: {task_type} | ID: {task_id[:8]}"
        )

    def task_end(self, task_type: str, task_id: str, success: bool, duration: float):
        status = "✅" if success else "❌"
        self._logger.info(
            f"[{self.agent_name}] {status} Task done: {task_type} | "
            f"ID: {task_id[:8]} | Duration: {duration:.2f}s"
        )

    def get_stats(self) -> dict:
        return {
            "agent":         self.agent_name,
            "error_count":   self.error_count,
            "warning_count": self.warning_count,
            "info_count":    self.info_count,
        }


# ──────────────────────────────────────────────────────────────
# SETUP FUNCTION - call once at startup
# ──────────────────────────────────────────────────────────────

def setup_logger(
    log_level:  str = "INFO",
    log_dir:    str = "logs",
    app_name:   str = "github-agent",
    json_logs:  bool = True,
) -> logging.Logger:
    """
    Setup the entire logging system.
    Call this ONCE at application startup (in main.py).

    Creates:
      - Colored console output
      - Daily rotating log file (plain text)
      - Daily rotating log file (JSON, for monitoring)

    Returns the root logger.
    """

    # Make sure log directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Remove any existing handlers (avoid duplicate logs)
    root_logger.handlers.clear()

    # ── 1. Console handler (colored) ──────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    console_formatter = ColoredFormatter(
        fmt=(
            "%(log_color)s%(asctime)s%(reset)s "
            "│ %(log_color)s%(levelname)-8s%(reset)s "
            "│ %(cyan)s%(name)-25s%(reset)s "
            "│ %(message)s"
        ),
        datefmt="%H:%M:%S",
        log_colors=LOG_COLORS,
        reset=True,
        style='%'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # ── 2. Plain text rotating file handler ───────────────────
    today = datetime.now().strftime("%Y-%m-%d")
    plain_file = os.path.join(log_dir, f"{app_name}-{today}.log")

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=plain_file,
        when="midnight",
        backupCount=30,          # Keep 30 days of logs
        encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    root_logger.addHandler(file_handler)

    # ── 3. JSON rotating file handler (for monitoring tools) ──
    if json_logs:
        json_file = os.path.join(log_dir, f"{app_name}-{today}.json.log")
        json_handler = logging.handlers.TimedRotatingFileHandler(
            filename=json_file,
            when="midnight",
            backupCount=30,
            encoding="utf-8"
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        root_logger.addHandler(json_handler)

    # Silence noisy third-party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("github").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    root_logger.info(
        f"📝 Logger initialized | Level: {log_level} | Dir: {log_dir}"
    )

    return root_logger


# ──────────────────────────────────────────────────────────────
# HELPER: Get a child logger quickly
# ──────────────────────────────────────────────────────────────

def get_logger(name: str) -> logging.Logger:
    """Shortcut to get a named logger."""
    return logging.getLogger(name)