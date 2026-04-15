# agents/__init__.py

from agents.issue_analyzer    import IssueAnalyzerAgent
from agents.code_fixer        import CodeFixerAgent
from agents.code_reviewer     import CodeReviewerAgent
from agents.security_scanner  import SecurityScannerAgent
from agents.test_writer       import TestWriterAgent
from agents.pr_manager        import PRManagerAgent
from agents.notification_agent import NotificationAgent
from agents.docs_writer       import DocsWriterAgent
from agents.dependency_agent  import DependencyAgent

__all__ = [
    "IssueAnalyzerAgent",
    "CodeFixerAgent",
    "CodeReviewerAgent",
    "SecurityScannerAgent",
    "TestWriterAgent",
    "PRManagerAgent",
    "NotificationAgent",
    "DocsWriterAgent",
    "DependencyAgent",
]


def get_all_agents() -> list:
    """
    Returns a list of every agent instance.
    Just import this and pass to orchestrator.register_agents().
    """
    return [
        IssueAnalyzerAgent(),
        CodeFixerAgent(),
        CodeReviewerAgent(),
        SecurityScannerAgent(),
        TestWriterAgent(),
        PRManagerAgent(),
        NotificationAgent(),
        DocsWriterAgent(),
        DependencyAgent(),
    ]