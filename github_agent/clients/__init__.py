# clients/__init__.py

from clients.github_client  import GitHubClient
from clients.ollama_client  import OllamaClient
from clients.webhook_client import WebhookClient

__all__ = ["GitHubClient", "OllamaClient", "WebhookClient"]