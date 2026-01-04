from typing import Dict, Any, List, Optional
import uuid
import time

class HumanReviewQueue:
    """
    Manages items that require human intervention.
    """
    def __init__(self):
        # In-memory store for demo. Use Redis/DB in production.
        self.queue: Dict[str, Dict[str, Any]] = {}

    def add_item(self, doc_id: str, reason: str, data: Any) -> str:
        """
        Add an item to the review queue.
        """
        review_id = str(uuid.uuid4())
        self.queue[review_id] = {
            "id": review_id,
            "doc_id": doc_id,
            "reason": reason,
            "data": data,
            "status": "pending",
            "created_at": time.time()
        }
        return review_id

    def get_pending_items(self) -> List[Dict[str, Any]]:
        """
        List all pending review items.
        """
        return [item for item in self.queue.values() if item["status"] == "pending"]

    def resolve_item(self, review_id: str, corrected_data: Any, reviewer: str):
        """
        Mark an item as resolved with corrected data.
        """
        if review_id in self.queue:
            self.queue[review_id]["status"] = "resolved"
            self.queue[review_id]["corrected_data"] = corrected_data
            self.queue[review_id]["reviewer"] = reviewer
            self.queue[review_id]["resolved_at"] = time.time()
