# clients/webhook_client.py
# Sends outbound webhooks and handles incoming GitHub webhooks

import hashlib
import hmac
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import requests
from flask import Flask, request, jsonify
from config.settings import Config


class WebhookClient:
    """
    Two responsibilities:
      1. SEND outbound webhooks (Slack, Discord, custom endpoints)
      2. RECEIVE incoming GitHub webhooks to trigger the agent
         in real-time instead of polling
    """

    def __init__(self):
        self.logger   = logging.getLogger("clients.webhook")
        self._handlers: Dict[str, List[Callable]] = {}

    # ──────────────────────────────────────────────────────────
    # OUTBOUND WEBHOOKS
    # ──────────────────────────────────────────────────────────

    def send(
        self,
        url:     str,
        payload: Dict,
        headers: Optional[Dict] = None,
        retries: int = 3,
    ) -> bool:
        """Generic webhook sender with retries."""
        headers = headers or {"Content-Type": "application/json"}

        for attempt in range(1, retries + 1):
            try:
                resp = requests.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=10,
                )
                if resp.status_code < 300:
                    self.logger.debug(f"Webhook sent → {url}")
                    return True
                self.logger.warning(
                    f"Webhook returned {resp.status_code} (attempt {attempt})"
                )
            except Exception as e:
                self.logger.error(
                    f"Webhook send error (attempt {attempt}): {e}"
                )

        return False

    # ── Slack ──────────────────────────────────────────────────

    def send_slack(
        self,
        message:  str,
        title:    str = "",
        color:    str = "good",
        fields:   Optional[List[Dict]] = None,
    ) -> bool:
        """Send a formatted Slack message."""
        if not Config.SLACK_WEBHOOK:
            return False

        payload: Dict[str, Any] = {"text": title or message}

        if title:
            payload["attachments"] = [
                {
                    "color":    color,
                    "text":     message,
                    "fields":   fields or [],
                    "footer":   "GitHub Agent System",
                    "mrkdwn_in": ["text"],
                }
            ]

        return self.send(Config.SLACK_WEBHOOK, payload)

    # ── Discord ────────────────────────────────────────────────

    def send_discord(
        self,
        message:     str,
        title:       str = "",
        color:       int = 5763719,   # green
        fields:      Optional[List[Dict]] = None,
    ) -> bool:
        """Send a Discord embed message."""
        if not Config.DISCORD_WEBHOOK:
            return False

        embed: Dict[str, Any] = {
            "description": message,
            "color":       color,
        }
        if title:
            embed["title"] = title
        if fields:
            embed["fields"] = fields

        return self.send(Config.DISCORD_WEBHOOK, {"embeds": [embed]})

    # ── Generic ────────────────────────────────────────────────

    def send_custom(self, url: str, data: Dict) -> bool:
        """Send to any custom webhook endpoint."""
        return self.send(url, data)

    # ──────────────────────────────────────────────────────────
    # INBOUND GITHUB WEBHOOKS
    # Real-time trigger: instead of polling every 5 min,
    # GitHub calls us the moment an issue is opened.
    # ──────────────────────────────────────────────────────────

    def on_event(self, event: str, fn: Callable):
        """
        Register a handler for a GitHub webhook event.

        event: e.g. 'issues', 'pull_request', 'push'
        fn: async or sync callable that receives the payload dict
        """
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(fn)
        self.logger.debug(f"Handler registered for event: {event}")

    def create_flask_endpoint(self, app: Flask, path: str = "/webhook"):
        """
        Attach a POST endpoint to an existing Flask app.
        GitHub should be configured to POST to this URL.
        """

        @app.route(path, methods=["POST"])
        def _github_webhook():
            # 1. Verify signature
            if not self._verify_signature(request):
                self.logger.warning("Webhook signature verification failed")
                return jsonify({"error": "Invalid signature"}), 403

            # 2. Parse event
            event   = request.headers.get("X-GitHub-Event", "")
            payload = request.get_json(force=True) or {}

            self.logger.info(f"Inbound webhook: {event}")

            # 3. Dispatch to handlers
            import asyncio
            for handler in self._handlers.get(event, []):
                try:
                    if asyncio.iscoroutinefunction(handler):
                        loop = asyncio.new_event_loop()
                        loop.run_until_complete(handler(payload))
                        loop.close()
                    else:
                        handler(payload)
                except Exception as e:
                    self.logger.error(f"Webhook handler error: {e}")

            return jsonify({"status": "ok"}), 200

        self.logger.info(f"Webhook endpoint registered: {path}")

    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _verify_signature(req) -> bool:
        """
        Validate the X-Hub-Signature-256 header from GitHub.
        If no secret is configured, skip verification.
        """
        secret = Config.GITHUB_WEBHOOK_SECRET
        if not secret:
            return True           # Not configured — allow all

        sig_header = req.headers.get("X-Hub-Signature-256", "")
        if not sig_header.startswith("sha256="):
            return False

        expected = hmac.new(
            secret.encode(),
            req.data,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(
            sig_header[len("sha256="):], expected
        )