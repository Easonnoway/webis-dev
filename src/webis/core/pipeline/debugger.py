import logging
import json
import os
from typing import Any, Dict
from webis.core.schema import PipelineContext, WebisDocument

logger = logging.getLogger(__name__)

class PipelineDebugger:
    """
    Helper class for debugging pipeline execution.
    Handles verbose logging and dumping intermediate states.
    """
    def __init__(self, context: PipelineContext):
        self.context = context
        self.debug_dir = os.path.join(context.output_dir or "debug_output", context.run_id)
        
        if self.context.is_debug:
            os.makedirs(self.debug_dir, exist_ok=True)

    def log_step(self, step_name: str, doc: WebisDocument, extra_info: Dict[str, Any] = None):
        """
        Log the state of a document at a specific pipeline step.
        """
        if not self.context.is_debug:
            return

        logger.info(f"[DEBUG] Step: {step_name} | Doc ID: {doc.id}")
        
        # Dump document state to JSON
        dump_path = os.path.join(self.debug_dir, f"{step_name}_{doc.id}.json")
        try:
            data = {
                "step": step_name,
                "doc": json.loads(doc.json()),
                "extra": extra_info or {}
            }
            with open(dump_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to dump debug info for {step_name}: {e}")

    def should_skip_execution(self) -> bool:
        """
        Check if we should skip actual execution (Dry Run).
        """
        if self.context.is_dry_run:
            logger.info("[DRY RUN] Skipping execution of heavy operation.")
            return True
        return False
