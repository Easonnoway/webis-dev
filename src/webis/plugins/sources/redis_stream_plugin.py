from typing import Any, Dict, List, Optional
import os
import redis
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class RedisStreamSourcePlugin(Plugin):
    """
    Plugin to consume items from a Redis Stream.
    """
    def __init__(self, stream_key: str, group_name: str, consumer_name: str, redis_url: str = None, batch_size: int = 10):
        self.stream_key = stream_key
        self.group_name = group_name
        self.consumer_name = consumer_name
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.batch_size = batch_size
        self.redis_client = None

    def initialize(self, context: PipelineContext):
        if not self.redis_client:
            self.redis_client = redis.from_url(self.redis_url)
            # Create consumer group if not exists
            try:
                self.redis_client.xgroup_create(self.stream_key, self.group_name, id="0", mkstream=True)
            except redis.exceptions.ResponseError as e:
                if "BUSYGROUP" not in str(e):
                    raise

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        if not self.redis_client:
             self.redis_client = redis.from_url(self.redis_url)

        # Read from stream
        try:
            entries = self.redis_client.xreadgroup(
                self.group_name,
                self.consumer_name,
                {self.stream_key: ">"},
                count=self.batch_size
            )
        except Exception as e:
            raise RuntimeError(f"Error reading from Redis Stream: {e}")

        items = []
        if entries:
            for stream, messages in entries:
                for message_id, data in messages:
                    # Convert bytes to string
                    item = {k.decode("utf-8"): v.decode("utf-8") for k, v in data.items()}
                    item["_stream_id"] = message_id.decode("utf-8")
                    items.append(item)
                    
                    # Ack immediately for simplicity, or let pipeline handle it?
                    # For now, ack here.
                    self.redis_client.xack(self.stream_key, self.group_name, message_id)

        # Merge with existing
        existing_items = context.get("items", [])
        if isinstance(existing_items, list):
            items.extend(existing_items)
            
        context.set("items", items)
        return {"items": items}
