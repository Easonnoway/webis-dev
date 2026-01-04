from typing import Any, Dict, List, Callable, Optional
import concurrent.futures
import logging
from webis.core.schema import WebisDocument, PipelineContext

logger = logging.getLogger(__name__)

class DistributedExecutor:
    """
    Manages distributed execution of pipeline tasks.
    Currently supports multi-threading/multi-processing locally.
    Could be extended to use Celery/Ray/Dask.
    """
    def __init__(self, max_workers: int = 4, mode: str = "thread"):
        self.max_workers = max_workers
        self.mode = mode
        self._executor: Optional[concurrent.futures.Executor] = None

    def __enter__(self):
        self._ensure_executor()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown()

    def _ensure_executor(self):
        if self._executor is None:
            if self.mode == "thread":
                self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)
            elif self.mode == "process":
                self._executor = concurrent.futures.ProcessPoolExecutor(max_workers=self.max_workers)
            else:
                # Sequential/Sync mode - no executor needed
                pass

    def shutdown(self, wait: bool = True):
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None

    def map(self, func: Callable[[Any], Any], items: List[Any]) -> List[Any]:
        """
        Applies func to items in parallel.
        """
        if self.mode not in ["thread", "process"]:
             return [func(item) for item in items]

        self._ensure_executor()
        if self._executor:
            return list(self._executor.map(func, items))
        return []

    def submit(self, func: Callable, *args, **kwargs) -> concurrent.futures.Future:
        """
        Submits a single task.
        """
        if self.mode not in ["thread", "process"]:
            # Emulate a Future for synchronous execution
            f = concurrent.futures.Future()
            try:
                result = func(*args, **kwargs)
                f.set_result(result)
            except Exception as e:
                f.set_exception(e)
            return f

        self._ensure_executor()
        if self._executor:
            return self._executor.submit(func, *args, **kwargs)
        
        # Fallback (should not happen if logic is correct)
        f = concurrent.futures.Future()
        f.set_exception(RuntimeError("Executor not initialized"))
        return f
