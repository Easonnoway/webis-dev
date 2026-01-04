"""
Webis Core - The kernel of Webis platform.

Contains fundamental abstractions:
- Schema definitions (WebisDocument, StructuredResult, etc.)
- Plugin interfaces (SourcePlugin, ProcessorPlugin)
- Pipeline engine
- LLM abstraction layer
"""

from webis.core.schema import WebisDocument, StructuredResult, PipelineContext
from webis.core.plugin import SourcePlugin, ProcessorPlugin, PluginRegistry

__all__ = [
    "WebisDocument",
    "StructuredResult",
    "PipelineContext",
    "SourcePlugin",
    "ProcessorPlugin",
    "PluginRegistry",
]
