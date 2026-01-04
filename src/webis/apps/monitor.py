import time
import schedule
import logging
from typing import List, Dict, Any
from webis.core.pipeline import Pipeline
from webis.core.plugin import PluginRegistry
from webis.plugins.notifications.slack_plugin import SlackNotificationPlugin
from webis.plugins.notifications.dingtalk_plugin import DingTalkNotificationPlugin
# Import other plugins as needed
from webis.plugins.sources.rss_plugin import RSSSourcePlugin

logger = logging.getLogger(__name__)

class WebisMonitor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.registry = PluginRegistry()
        self._setup_plugins()
        self.pipeline = Pipeline(registry=self.registry, config=config)
        self._setup_pipeline()

    def _setup_plugins(self):
        # Register notification plugins
        self.registry.register(SlackNotificationPlugin())
        self.registry.register(DingTalkNotificationPlugin())
        # Register source plugins
        self.registry.register(RSSSourcePlugin())
        # Add more as needed

    def _setup_pipeline(self):
        # Configure pipeline based on config
        # This is a simplified example
        self.pipeline.add_source("rss_source")
        # Add processors...
        
    def check_and_notify(self):
        logger.info("Running monitor check...")
        try:
            result = self.pipeline.run("Monitor Check")
            
            # Analyze result for keywords
            keywords = self.config.get("keywords", [])
            found_items = []
            
            for doc in result.documents:
                content = doc.content.lower()
                for keyword in keywords:
                    if keyword.lower() in content:
                        found_items.append((keyword, doc))
            
            if found_items:
                message = "Found keywords:\n"
                for keyword, doc in found_items:
                    message += f"- '{keyword}' in {doc.meta.title or doc.meta.url}\n"
                
                self._send_notifications(message)
                
        except Exception as e:
            logger.error(f"Monitor check failed: {e}")

    def _send_notifications(self, message: str):
        # Send to all registered notification plugins
        # In a real app, we might want to select which ones to use
        if self.config.get("slack_webhook_url"):
            plugin = self.registry._notifications.get("slack_notification") # Accessing internal dict for now
            if not plugin:
                 plugin = SlackNotificationPlugin() # Fallback
            plugin.send(message, title="Webis Monitor Alert")
            
        if self.config.get("dingtalk_webhook_url"):
             plugin = self.registry._notifications.get("dingtalk_notification")
             if not plugin:
                 plugin = DingTalkNotificationPlugin()
             plugin.send(message, title="Webis Monitor Alert")

    def start(self):
        interval = self.config.get("interval_minutes", 60)
        schedule.every(interval).minutes.do(self.check_and_notify)
        
        logger.info(f"Monitor started. Checking every {interval} minutes.")
        
        # Run once immediately
        self.check_and_notify()
        
        while True:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    # Example usage
    config = {
        "rss_feeds": ["https://news.ycombinator.com/rss"],
        "keywords": ["python", "ai", "llm"],
        "interval_minutes": 10,
        # "slack_webhook_url": "...",
        # "dingtalk_webhook_url": "..."
    }
    monitor = WebisMonitor(config)
    monitor.start()
