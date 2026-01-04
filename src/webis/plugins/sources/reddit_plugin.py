from typing import Any, Dict, List, Optional
import os
import praw
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class RedditSourcePlugin(Plugin):
    """
    Plugin to fetch items from Reddit.
    """
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None, subreddit: str = "all", limit: int = 10):
        self.client_id = client_id or os.getenv("REDDIT_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("REDDIT_CLIENT_SECRET")
        self.user_agent = user_agent or os.getenv("REDDIT_USER_AGENT", "webis-bot")
        self.subreddit_name = subreddit
        self.limit = limit
        self.reddit = None

    def initialize(self, context: PipelineContext):
        if not self.client_id:
            self.client_id = context.config.get("reddit_client_id")
        if not self.client_secret:
            self.client_secret = context.config.get("reddit_client_secret")
        
        if self.client_id and self.client_secret:
            self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        if not self.reddit:
             # Try to init again if keys were passed in kwargs?
             # For now, just fail or return empty
             if not self.client_id:
                 raise ValueError("Reddit client_id and client_secret are required")
             self.reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent
            )

        subreddit_name = kwargs.get("subreddit") or self.subreddit_name
        limit = kwargs.get("limit") or self.limit
        
        subreddit = self.reddit.subreddit(subreddit_name)
        posts = []
        
        try:
            for submission in subreddit.new(limit=limit):
                post = {
                    "title": submission.title,
                    "url": submission.url,
                    "text": submission.selftext,
                    "score": submission.score,
                    "id": submission.id,
                    "created_utc": submission.created_utc,
                    "source": "reddit"
                }
                posts.append(post)
        except Exception as e:
            raise RuntimeError(f"Error fetching from Reddit: {e}")

        # Merge with existing
        existing_items = context.get("items", [])
        if isinstance(existing_items, list):
            posts.extend(existing_items)
            
        context.set("items", posts)
        return {"items": posts}
