import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

try:
    print("Starting import test...")
    from webis.core.memory.retriever import HybridRetriever
    print("HybridRetriever imported")
    from webis.core.memory.deduplication import Deduplicator
    print("Deduplicator imported")
    from webis.core.celery_app import celery_app
    print("Celery app imported")
    from webis.core.worker import run_pipeline_task
    print("Worker imported")
    print("All imports successful")
except Exception as e:
    print(f"Import failed: {e}")
