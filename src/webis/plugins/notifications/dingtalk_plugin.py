from typing import Optional
import os
import requests
import json
import hmac
import hashlib
import base64
import time
import urllib.parse
from webis.core.plugin import NotificationPlugin
from webis.core.schema import PipelineContext

class DingTalkNotificationPlugin(NotificationPlugin):
    """
    Plugin to send notifications to DingTalk via Webhook.
    """
    def __init__(self, webhook_url: Optional[str] = None, secret: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("DINGTALK_WEBHOOK_URL")
        self.secret = secret or os.getenv("DINGTALK_SECRET")

    def initialize(self, context: PipelineContext):
        if not self.webhook_url:
            self.webhook_url = context.config.get("dingtalk_webhook_url")
        if not self.secret:
            self.secret = context.config.get("dingtalk_secret")

    def _sign(self):
        timestamp = str(round(time.time() * 1000))
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = '{}\n{}'.format(timestamp, self.secret)
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        return timestamp, sign

    def send(
        self,
        message: str,
        title: Optional[str] = None,
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> bool:
        if not self.webhook_url:
            print("DingTalk webhook URL not configured")
            return False

        url = self.webhook_url
        if self.secret:
            timestamp, sign = self._sign()
            url = f"{url}&timestamp={timestamp}&sign={sign}"

        payload = {
            "msgtype": "markdown",
            "markdown": {
                "title": title or "Webis Notification",
                "text": f"### {title or 'Webis Notification'}\n\n{message}"
            }
        }

        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send DingTalk notification: {e}")
            return False
