from typing import Any, Dict, Iterator, List, Optional
import time
import random
from webis.core.plugin import SourcePlugin, PluginRegistry
from webis.core.schema import WebisDocument, PipelineContext

class SmartFetcherPlugin(SourcePlugin):
    """
    A meta-source plugin that attempts to fetch data using multiple strategies
    or underlying plugins, with retries and fallback.
    """
    name = "smart_fetcher"
    
    def __init__(self, strategies: List[str] = None):
        self.strategies = strategies or ["requests", "selenium", "api"]
        self.registry = None

    def initialize(self, context: PipelineContext):
        # In a real implementation, we would need access to the registry to call other plugins
        # For now, we'll simulate strategies
        pass

    def fetch(self, query: str, **kwargs) -> Iterator[WebisDocument]:
        # Simulate trying different strategies
        for strategy in self.strategies:
            try:
                print(f"SmartFetcher: Trying strategy '{strategy}'...")
                yield from self._execute_strategy(strategy, query, **kwargs)
                print(f"SmartFetcher: Strategy '{strategy}' succeeded.")
                return
            except Exception as e:
                print(f"SmartFetcher: Strategy '{strategy}' failed: {e}")
                time.sleep(random.uniform(0.5, 2.0)) # Backoff
        
        raise RuntimeError("All fetch strategies failed.")

    def _execute_strategy(self, strategy: str, query: str, **kwargs):
        # Mock implementation of strategies
        if strategy == "requests":
            # Simulate failure sometimes
            if random.random() < 0.5:
                raise ConnectionError("Connection reset")
            # Simulate success
            from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata
            yield WebisDocument(
                content=f"Content fetched via {strategy} for {query}",
                doc_type=DocumentType.HTML,
                meta=DocumentMetadata(url="http://example.com", source_plugin=self.name)
            )
        elif strategy == "selenium":
             # Simulate success
            from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata
            yield WebisDocument(
                content=f"Content fetched via {strategy} (headless browser) for {query}",
                doc_type=DocumentType.HTML,
                meta=DocumentMetadata(url="http://example.com", source_plugin=self.name)
            )
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
