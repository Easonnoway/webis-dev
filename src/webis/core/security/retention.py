import os
import time
import logging
from typing import List

logger = logging.getLogger(__name__)

class DataRetentionPolicy:
    """
    Enforces data retention rules by cleaning up old data.
    """
    def __init__(self, retention_days: int = 30, data_dir: str = "data"):
        self.retention_days = retention_days
        self.data_dir = data_dir

    def run_cleanup(self):
        """
        Delete files older than retention_days.
        """
        logger.info(f"Starting data retention cleanup (older than {self.retention_days} days)...")
        
        cutoff_time = time.time() - (self.retention_days * 86400)
        deleted_count = 0
        
        if not os.path.exists(self.data_dir):
            logger.warning(f"Data directory {self.data_dir} does not exist.")
            return

        for root, dirs, files in os.walk(self.data_dir):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    stat = os.stat(file_path)
                    if stat.st_mtime < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
                        logger.debug(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")
                    
        logger.info(f"Cleanup completed. Deleted {deleted_count} files.")
