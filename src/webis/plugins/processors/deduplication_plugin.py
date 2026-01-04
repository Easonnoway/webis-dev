from typing import Any, Dict, List, Optional, Set
import os
import json
import hashlib
from webis.core.pipeline import PipelineContext
from webis.core.plugin import Plugin

class DeduplicationPlugin(Plugin):
    """
    Plugin to filter out duplicate items based on URL or content hash.
    """
    def __init__(self, state_file: str = "dedup_state.json", key_field: str = "url"):
        self.state_file = state_file
        self.key_field = key_field
        self.seen_keys: Set[str] = set()

    def initialize(self, context: PipelineContext):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.seen_keys = set(json.load(f))
            except Exception:
                self.seen_keys = set()

    def run(self, context: PipelineContext, **kwargs) -> Dict[str, Any]:
        items = kwargs.get("items") or context.get("items")
        if not items:
            return {"items": [], "filtered_count": 0}

        new_items = []
        for item in items:
            key = item.get(self.key_field)
            if not key:
                # If key field missing, try to hash the content if available
                content = item.get("content") or item.get("text")
                if content:
                    key = hashlib.md5(content.encode("utf-8")).hexdigest()
                else:
                    continue
            
            if key not in self.seen_keys:
                self.seen_keys.add(key)
                new_items.append(item)

        # Save state
        self._save_state()

        context.set("items", new_items)
        return {"items": new_items, "filtered_count": len(items) - len(new_items)}

    def _save_state(self):
        with open(self.state_file, "w") as f:
            json.dump(list(self.seen_keys), f)
