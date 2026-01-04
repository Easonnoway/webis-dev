from typing import Optional
import os
import requests
from webis.core.plugin import NotificationPlugin
from webis.core.schema import PipelineContext

class SlackNotificationPlugin(NotificationPlugin):
    """
    Plugin to send notifications to Slack via Webhook.
    """
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")

    def initialize(self, context: PipelineContext):
        if not self.webhook_url:
            self.webhook_url = context.config.get("slack_webhook_url")

    def send(
        self,
        message: str,
        title: Optional[str] = None,
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> bool:
        if not self.webhook_url:
            print("Slack webhook URL not configured")
            return False

        payload = {"text": message}
        if title:
            payload["blocks"] = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": message
                    }
                }
            ]

        try:
            response = requests.post(self.webhook_url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Slack notification: {e}")
            return False
