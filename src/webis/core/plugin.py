"""
Plugin system for Webis platform.

Provides base classes and registry for source plugins (data acquisition)
and processor plugins (data transformation).

Example:
    >>> from webis.core.plugin import SourcePlugin, PluginRegistry
    >>> 
    >>> class MySearchPlugin(SourcePlugin):
    ...     name = "my_search"
    ...     def fetch(self, query, **kwargs):
    ...         yield WebisDocument(content="...")
    >>> 
    >>> registry = PluginRegistry()
    >>> registry.register(MySearchPlugin())
"""

from __future__ import annotations

import importlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional, Type, TypeVar

from webis.core.schema import WebisDocument, PipelineContext

logger = logging.getLogger(__name__)


@dataclass
class PluginMetadata:
    """Metadata describing a plugin."""
    
    name: str
    version: str = "0.1.0"
    description: str = ""
    author: str = ""
    
    # Capabilities and requirements
    capabilities: List[str] = field(default_factory=list)
    required_env_vars: List[str] = field(default_factory=list)
    required_packages: List[str] = field(default_factory=list)
    
    # Plugin categorization
    plugin_type: str = "generic"  # source, processor, extractor, etc.
    is_builtin: bool = False


class BasePlugin(ABC):
    """
    Base class for all Webis plugins.
    
    Every plugin must define:
    - name: Unique identifier
    - description: Human-readable description
    - metadata: Plugin metadata
    """
    
    name: str = "base_plugin"
    description: str = "Base plugin class"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._initialized = False
    
    @property
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        return PluginMetadata(
            name=self.name,
            description=self.description,
        )
    
    def initialize(self, context: Optional[PipelineContext] = None) -> None:
        """
        Initialize the plugin with optional context.
        
        Called once before the plugin is used. Override to perform
        setup tasks like connecting to external services.
        """
        self._initialized = True
    
    def cleanup(self) -> None:
        """
        Clean up resources.
        
        Called when the plugin is no longer needed. Override to
        close connections, release resources, etc.
        """
        self._initialized = False
    
    def validate_config(self) -> List[str]:
        """
        Validate plugin configuration.
        
        Returns:
            List of validation error messages. Empty list if valid.
        """
        return []
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name={self.name})>"


class SourcePlugin(BasePlugin):
    """
    Base class for data source plugins.
    
    Source plugins are responsible for fetching data from external sources
    (web, APIs, files, etc.) and converting them to WebisDocument objects.
    
    Example:
        >>> class NewsApiPlugin(SourcePlugin):
        ...     name = "news_api"
        ...     description = "Fetch news from NewsAPI"
        ...     
        ...     def fetch(self, query: str, **kwargs) -> Iterator[WebisDocument]:
        ...         # Fetch from API
        ...         for article in api.search(query):
        ...             yield WebisDocument(
        ...                 content=article.content,
        ...                 doc_type=DocumentType.HTML,
        ...                 meta=DocumentMetadata(url=article.url)
        ...             )
    """
    
    # Plugin type categorization
    source_type: str = "generic"  # web, api, file, stream, etc.
    
    # Capabilities
    supports_pagination: bool = False
    supports_incremental: bool = False
    max_results_per_call: Optional[int] = None
    
    @abstractmethod
    def fetch(
        self, 
        query: str, 
        limit: int = 10,
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        """
        Fetch documents from the source.
        
        Args:
            query: Search query or task description
            limit: Maximum number of documents to fetch
            context: Pipeline context for logging and config
            **kwargs: Additional source-specific parameters
            
        Yields:
            WebisDocument objects
        """
        raise NotImplementedError
    
    def estimate_count(self, query: str, **kwargs) -> Optional[int]:
        """
        Estimate the number of results for a query.
        
        Returns None if estimation is not supported.
        """
        return None


class ProcessorPlugin(BasePlugin):
    """
    Base class for document processing plugins.
    
    Processor plugins transform WebisDocument objects, such as:
    - Cleaning HTML to plain text
    - Extracting text from PDFs
    - Redacting PII
    - Chunking text for embedding
    
    Example:
        >>> class HtmlCleanerPlugin(ProcessorPlugin):
        ...     name = "html_cleaner"
        ...     description = "Extract clean text from HTML"
        ...     
        ...     def process(self, doc: WebisDocument, **kwargs) -> WebisDocument:
        ...         doc.clean_content = extract_text(doc.content)
        ...         doc.add_processing_step(self.name)
        ...         return doc
    """
    
    # Which document types this processor can handle
    supported_types: List[str] = []
    
    # Processing behavior
    modifies_content: bool = True
    is_filter: bool = False  # If True, can return None to filter out docs
    
    @abstractmethod
    def process(
        self, 
        doc: WebisDocument,
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Optional[WebisDocument]:
        """
        Process a single document.
        
        Args:
            doc: Input document
            context: Pipeline context
            **kwargs: Additional processor-specific parameters
            
        Returns:
            Processed document, or None if filtered out
        """
        raise NotImplementedError
    
    def process_batch(
        self, 
        docs: List[WebisDocument],
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> List[WebisDocument]:
        """
        Process multiple documents.
        
        Default implementation calls process() for each document.
        Override for batch-optimized processing.
        """
        results = []
        for doc in docs:
            processed = self.process(doc, context=context, **kwargs)
            if processed is not None:
                results.append(processed)
        return results
    
    def can_process(self, doc: WebisDocument) -> bool:
        """Check if this processor can handle the given document type."""
        if not self.supported_types:
            return True
        return doc.doc_type.value in self.supported_types


class ExtractorPlugin(BasePlugin):
    """
    Base class for structured extraction plugins.
    
    Extractor plugins use LLMs to extract structured data from documents.
    """
    
    # Schema this extractor produces
    output_schema: Optional[Dict[str, Any]] = None
    
    @abstractmethod
    def extract(
        self,
        docs: List[WebisDocument],
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> "StructuredResult":
        """
        Extract structured data from documents.
        
        Args:
            docs: Input documents
            context: Pipeline context
            **kwargs: Additional parameters
            
        Returns:
            StructuredResult with extracted data
        """
        raise NotImplementedError


class NotificationPlugin(BasePlugin):
    """
    Base class for notification plugins.
    
    Used to send alerts or reports to external systems (Slack, Email, etc.).
    """
    
    @abstractmethod
    def send(
        self,
        message: str,
        title: Optional[str] = None,
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> bool:
        """
        Send a notification.
        
        Args:
            message: Body of the notification
            title: Optional title
            context: Pipeline context
            **kwargs: Additional parameters
            
        Returns:
            True if sent successfully
        """
        raise NotImplementedError


# Type variable for plugin types
P = TypeVar("P", bound=BasePlugin)


class PluginRegistry:
    """
    Registry for managing Webis plugins.
    
    Supports:
    - Manual registration
    - Dynamic loading from module paths
    - Plugin discovery
    
    Example:
        >>> registry = PluginRegistry()
        >>> registry.register(MyPlugin())
        >>> plugin = registry.get("my_plugin")
    """
    
    def __init__(self):
        self._sources: Dict[str, SourcePlugin] = {}
        self._processors: Dict[str, ProcessorPlugin] = {}
        self._extractors: Dict[str, ExtractorPlugin] = {}
        self._notifications: Dict[str, NotificationPlugin] = {}
        self._all: Dict[str, BasePlugin] = {}
    
    def register(self, plugin: BasePlugin) -> None:
        """
        Register a plugin instance.
        
        Args:
            plugin: Plugin instance to register
        """
        if plugin.name in self._all:
            logger.warning(f"Plugin '{plugin.name}' already registered, overwriting")
        
        self._all[plugin.name] = plugin
        
        if isinstance(plugin, SourcePlugin):
            self._sources[plugin.name] = plugin
        elif isinstance(plugin, ProcessorPlugin):
            self._processors[plugin.name] = plugin
        elif isinstance(plugin, ExtractorPlugin):
            self._extractors[plugin.name] = plugin
        elif isinstance(plugin, NotificationPlugin):
            self._notifications[plugin.name] = plugin
        
        logger.info(f"Registered plugin: {plugin.name}")
    
    def register_class(self, plugin_class: Type[P], **init_kwargs) -> P:
        """
        Register a plugin class (instantiates it).
        
        Args:
            plugin_class: Plugin class to instantiate and register
            **init_kwargs: Arguments to pass to plugin constructor
            
        Returns:
            The instantiated plugin
        """
        plugin = plugin_class(**init_kwargs)
        self.register(plugin)
        return plugin
    
    def load_from_path(self, module_path: str, class_name: Optional[str] = None) -> BasePlugin:
        """
        Dynamically load and register a plugin from a module path.
        
        Args:
            module_path: Python module path (e.g., "webis.plugins.sources.news")
            class_name: Class name to load (optional, will find first Plugin subclass)
            
        Returns:
            The loaded plugin instance
        """
        module = importlib.import_module(module_path)
        
        if class_name:
            plugin_class = getattr(module, class_name)
        else:
            # Find first BasePlugin subclass
            plugin_class = None
            for name in dir(module):
                obj = getattr(module, name)
                if (
                    isinstance(obj, type) 
                    and issubclass(obj, BasePlugin) 
                    and obj is not BasePlugin
                    and obj is not SourcePlugin
                    and obj is not ProcessorPlugin
                    and obj is not ExtractorPlugin
                ):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                raise ValueError(f"No plugin class found in {module_path}")
        
        return self.register_class(plugin_class)
    
    def get(self, name: str) -> Optional[BasePlugin]:
        """Get a plugin by name."""
        return self._all.get(name)
    
    def get_source(self, name: str) -> Optional[SourcePlugin]:
        """Get a source plugin by name."""
        return self._sources.get(name)
    
    def get_processor(self, name: str) -> Optional[ProcessorPlugin]:
        """Get a processor plugin by name."""
        return self._processors.get(name)
    
    def get_extractor(self, name: str) -> Optional[ExtractorPlugin]:
        """Get an extractor plugin by name."""
        return self._extractors.get(name)
    
    def list_sources(self) -> List[str]:
        """List all registered source plugin names."""
        return list(self._sources.keys())
    
    def list_processors(self) -> List[str]:
        """List all registered processor plugin names."""
        return list(self._processors.keys())
    
    def list_extractors(self) -> List[str]:
        """List all registered extractor plugin names."""
        return list(self._extractors.keys())
    
    def list_all(self) -> List[str]:
        """List all registered plugin names."""
        return list(self._all.keys())
    
    def unregister(self, name: str) -> bool:
        """
        Unregister a plugin by name.
        
        Returns True if the plugin was found and removed.
        """
        plugin = self._all.pop(name, None)
        if plugin is None:
            return False
        
        self._sources.pop(name, None)
        self._processors.pop(name, None)
        self._extractors.pop(name, None)
        self._notifications.pop(name, None)
        
        plugin.cleanup()
        return True
    
    def clear(self) -> None:
        """Unregister all plugins."""
        for plugin in self._all.values():
            plugin.cleanup()
        
        self._all.clear()
        self._sources.clear()
        self._processors.clear()
        self._extractors.clear()
        self._notifications.clear()


# Global default registry
_default_registry: Optional[PluginRegistry] = None


def get_default_registry() -> PluginRegistry:
    """Get the default global plugin registry."""
    global _default_registry
    if _default_registry is None:
        _default_registry = PluginRegistry()
    return _default_registry


# Alias for backward compatibility or convenience
Plugin = BasePlugin

__all__ = [
    "PluginMetadata",
    "BasePlugin",
    "Plugin",
    "SourcePlugin",
    "ProcessorPlugin",
    "ExtractorPlugin",
    "NotificationPlugin",
    "PluginRegistry",
    "get_default_registry",
]
