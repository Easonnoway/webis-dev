import json
import os
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CheckpointManager:
    """
    Manages pipeline checkpoints to allow resuming interrupted tasks.
    """
    def __init__(self, storage_dir: str = ".checkpoints"):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

    def _get_path(self, run_id: str) -> str:
        return os.path.join(self.storage_dir, f"{run_id}.json")

    def save_checkpoint(self, run_id: str, state: Dict[str, Any]):
        """
        Save the current state of a pipeline run.
        """
        path = self._get_path(run_id)
        try:
            with open(path, "w") as f:
                json.dump(state, f, indent=2)
            logger.debug(f"Checkpoint saved for run {run_id}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint for {run_id}: {e}")

    def load_checkpoint(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        Load a saved state for a pipeline run.
        """
        path = self._get_path(run_id)
        if not os.path.exists(path):
            return None
        
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load checkpoint for {run_id}: {e}")
            return None

    def clear_checkpoint(self, run_id: str):
        """
        Remove a checkpoint after successful completion.
        """
        path = self._get_path(run_id)
        if os.path.exists(path):
            os.remove(path)
