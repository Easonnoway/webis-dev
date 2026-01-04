from typing import Optional, Dict, Any, ContextManager
import time
import logging
import functools
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class Span:
    def __init__(self, name: str, trace_id: str, parent_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.parent_id = parent_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.status = "OK"

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def set_status(self, status: str):
        self.status = status

    def end(self):
        self.end_time = time.time()
        duration = (self.end_time - self.start_time) * 1000
        logger.info(f"[Trace: {self.trace_id}] Span '{self.name}' finished in {duration:.2f}ms. Status: {self.status}")

class Tracer:
    """
    A simple abstraction for tracing. 
    In production, this would wrap OpenTelemetry or LangSmith.
    """
    def __init__(self, service_name: str = "webis"):
        self.service_name = service_name

    @contextmanager
    def start_span(self, name: str, trace_id: Optional[str] = None) -> ContextManager[Span]:
        if not trace_id:
            import uuid
            trace_id = str(uuid.uuid4())
        
        span = Span(name, trace_id)
        try:
            yield span
        except Exception as e:
            span.set_status("ERROR")
            span.set_attribute("error.message", str(e))
            raise
        finally:
            span.end()

    def trace(self, name: Optional[str] = None):
        """Decorator to trace a function."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                span_name = name or func.__name__
                with self.start_span(span_name) as span:
                    # Try to capture args if simple types
                    span.set_attribute("args", str(args)[:100]) 
                    return func(*args, **kwargs)
            return wrapper
        return decorator

# Global tracer instance
tracer = Tracer()
