import signal
from contextlib import contextmanager
import threading
import sys

class TimeoutError(Exception):
    pass

@contextmanager
def timeout(seconds: int):
    """
    Context manager for timeout.
    Uses signal.alarm on Unix-based systems.
    """
    if seconds <= 0:
        yield
        return

    def signal_handler(signum, frame):
        raise TimeoutError(f"Execution timed out after {seconds} seconds")

    # Register the signal function handler
    original_handler = signal.signal(signal.SIGALRM, signal_handler)
    
    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)

def timeout_decorator(seconds: int):
    """
    Decorator to add timeout to a function.
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            with timeout(seconds):
                return func(*args, **kwargs)
        return wrapper
    return decorator
