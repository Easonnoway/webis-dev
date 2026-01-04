import logging
import time
import json
from typing import Any

logger = logging.getLogger("webis.audit")

class AuditLogger:
    """
    Logs security-relevant events for compliance.
    """
    def __init__(self, log_file: str = "audit.log"):
        self.log_file = log_file
        # Ensure file exists
        with open(self.log_file, "a"):
            pass

    def log_event(self, event_type: str, user: str, resource: str, details: Any = None):
        """
        Log an audit event.
        """
        entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "user": user,
            "resource": resource,
            "details": details or {}
        }
        
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            # Fallback to standard logger if file write fails
            logger.error(f"Failed to write audit log: {e}")
            logger.info(f"AUDIT EVENT: {json.dumps(entry)}")

# Global instance
audit_logger = AuditLogger()
