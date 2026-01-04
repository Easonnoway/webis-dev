from typing import Any, Dict, List
import feedparser
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class RSSSourcePlugin(Plugin):
    """
    Plugin to fetch items from RSS/Atom feeds.
    """
    def __init__(self, feed_urls: List[str] = None):
        self.feed_urls = feed_urls or []

    def initialize(self, context: PipelineContext):
        # Allow overriding feed_urls from context config
        if not self.feed_urls:
            self.feed_urls = context.config.get("rss_feeds", [])

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        # Allow passing feed_urls in run kwargs
        feed_urls = kwargs.get("feed_urls") or self.feed_urls
        
        all_entries = []
        for url in feed_urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries:
                    item = {
                        "title": entry.get("title"),
                        "url": entry.get("link"),
                        "published": entry.get("published"),
                        "summary": entry.get("summary"),
                        "source": url,
                        "content": entry.get("summary") # Use summary as content for now
                    }
                    all_entries.append(item)
            except Exception as e:
                print(f"Error fetching RSS feed {url}: {e}")
        
        # Merge with existing items if any
        existing_items = context.get("items", [])
        if isinstance(existing_items, list):
            all_entries.extend(existing_items)
            
        context.set("items", all_entries)
        return {"items": all_entries}
