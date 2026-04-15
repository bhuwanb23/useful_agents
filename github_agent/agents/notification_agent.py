# agents/notification_agent.py

import json
import logging
import requests
from typing import Dict, List, Optional
from core.base_agent import BaseAgent
from config.settings import Config


class NotificationAgent(BaseAgent):
    """
    Sends notifications about agent actions to various channels:
    - GitHub issue comments
    - Slack webhooks
    - Discord webhooks
    """
    
    def __init__(self):
        super().__init__(
            name="notification_agent",
            description="Sends notifications about agent actions"
        )
        self.capabilities = ["notify", "comment_on_issue", "send_webhook"]
    
    def can_handle(self, task: Dict) -> bool:
        return task.get('type') == 'notify'
    
    async def execute(self, task: Dict) -> Dict:
        notification_type = task.get('type')
        issue = task.get('issue', {})
        
        self.logger.info(f"📧 Sending notification for issue #{issue.get('number')}")
        
        results = {
            "issue": issue,
            "github_comment": False,
            "slack": False,
            "discord": False,
        }
        
        # Comment on GitHub issue
        if task.get('comment_on_issue', True):
            comment_body = self._format_comment(task)
            results['github_comment'] = await self._comment_on_issue(
                issue.get('number'),
                comment_body
            )
        
        # Send to Slack
        if Config.SLACK_WEBHOOK:
            results['slack'] = await self._send_slack_notification(task)
        
        # Send to Discord
        if Config.DISCORD_WEBHOOK:
            results['discord'] = await self._send_discord_notification(task)
        
        self.logger.info(f"✅ Notifications sent for issue #{issue.get('number')}")
        
        return results
    
    async def _comment_on_issue(self, issue_number: int, body: str) -> bool:
        """Post a comment on the GitHub issue."""
        try:
            success = self.github.add_issue_comment(issue_number, body)
            if success:
                self.logger.info(f"💬 Commented on issue #{issue_number}")
            return success
        except Exception as e:
            self.logger.error(f"Failed to comment on issue #{issue_number}: {e}")
            return False
    
    async def _send_slack_notification(self, task: Dict) -> bool:
        """Send notification to Slack webhook."""
        try:
            issue = task.get('issue', {})
            pr_url = task.get('pr_url', '')
            
            if pr_url:
                message = {
                    "text": f"🤖 *GitHub Agent*",
                    "blocks": [
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn",
                                "text": (
                                    f"🎉 *PR Created*\n"
                                    f"*Issue:* #{issue.get('number')} - {issue.get('title')}\n"
                                    f"*PR:* <{pr_url}|View PR>"
                                )
                            }
                        }
                    ]
                }
            else:
                message = {
                    "text": f"🤖 GitHub Agent Update: Issue #{issue.get('number')}"
                }
            
            response = requests.post(
                Config.SLACK_WEBHOOK,
                json=message,
                timeout=10
            )
            
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Slack notification failed: {e}")
            return False
    
    async def _send_discord_notification(self, task: Dict) -> bool:
        """Send notification to Discord webhook."""
        try:
            issue = task.get('issue', {})
            pr_url = task.get('pr_url', '')
            
            if pr_url:
                embed = {
                    "title": "🎉 PR Created",
                    "description": (
                        f"**Issue:** #{issue.get('number')} - {issue.get('title')}\n"
                        f"**PR:** [View PR]({pr_url})"
                    ),
                    "color": 3066993,  # Green
                }
            else:
                embed = {
                    "title": f"🤖 GitHub Agent Update",
                    "description": f"Issue #{issue.get('number')}",
                    "color": 15158332,  # Red
                }
            
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(
                Config.DISCORD_WEBHOOK,
                json=payload,
                timeout=10
            )
            
            return response.status_code == 204  # Discord returns 204 No Content
            
        except Exception as e:
            self.logger.error(f"Discord notification failed: {e}")
            return False
    
    def _format_comment(self, task: Dict) -> str:
        """Format a comment for GitHub issue."""
        issue = task.get('issue', {})
        notification_type = task.get('notification_type', 'update')
        pr_url = task.get('pr_url', '')
        
        if notification_type == 'pr_created' and pr_url:
            return (
                f"## 🤖 GitHub Agent - PR Created\n\n"
                f"A pull request has been automatically created to address this issue.\n\n"
                f"**PR:** {pr_url}\n\n"
                f"This PR was generated by the GitHub Agent system using AI-powered code fixes.\n"
                f"Please review the changes before merging."
            )
        elif notification_type == 'security_blocked':
            return (
                f"## 🔒 Security Scan Failed\n\n"
                f"The automated fix could not be deployed due to security concerns.\n\n"
                f"Please review the issue manually."
            )
        elif notification_type == 'review_rejected':
            return (
                f"## ❌ Code Review Failed\n\n"
                f"The automated fix did not pass code review.\n\n"
                f"Please review the issue manually."
            )
        else:
            return (
                f"## 🤖 GitHub Agent Update\n\n"
                f"This issue is being processed by the GitHub Agent system."
            )
