from typing import List, Callable, Any, Awaitable
import asyncio
import time
import logging

logger = logging.getLogger(__name__)

class BatchProcessor:
    """
    Accumulates items and processes them in batches to optimize LLM usage.
    """
    def __init__(self, 
                 processor_func: Callable[[List[Any]], Awaitable[List[Any]]], 
                 batch_size: int = 10, 
                 linger_ms: int = 100):
        self.processor_func = processor_func
        self.batch_size = batch_size
        self.linger_ms = linger_ms / 1000.0  # Convert to seconds
        self.queue = asyncio.Queue()
        self._running = False
        self._task = None

    async def start(self):
        self._running = True
        self._task = asyncio.create_task(self._process_loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def add(self, item: Any) -> asyncio.Future:
        future = asyncio.Future()
        await self.queue.put((item, future))
        return future

    async def _process_loop(self):
        while self._running:
            batch = []
            futures = []
            
            try:
                # Wait for the first item indefinitely (or until cancelled)
                item, future = await self.queue.get()
                batch.append(item)
                futures.append(future)
                
                # Calculate deadline for the batch
                deadline = time.time() + self.linger_ms
                
                # Try to fill the batch
                while len(batch) < self.batch_size:
                    remaining = deadline - time.time()
                    if remaining <= 0:
                        break
                        
                    try:
                        item, future = await asyncio.wait_for(self.queue.get(), timeout=remaining)
                        batch.append(item)
                        futures.append(future)
                    except asyncio.TimeoutError:
                        break
                
                # Process the batch
                if batch:
                    try:
                        results = await self.processor_func(batch)
                        for i, result in enumerate(results):
                            if not futures[i].done():
                                futures[i].set_result(result)
                    except Exception as e:
                        logger.error(f"Batch processing failed: {e}")
                        for f in futures:
                            if not f.done():
                                f.set_exception(e)
                                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in batch loop: {e}")
                await asyncio.sleep(1) # Prevent tight loop on error
