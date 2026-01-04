"""
Webis - From Web to Wisdom: Your AI-Powered Knowledge Pipeline

A comprehensive platform for web data acquisition, intelligent processing,
and structured knowledge extraction powered by Large Language Models.
"""

__version__ = "2.0.0-alpha.1"
__author__ = "Webis Team"
__license__ = "Apache-2.0"

from webis.core.schema import WebisDocument, StructuredResult, PipelineContext
from webis.core.pipeline import Pipeline

__all__ = [
    "__version__",
    "WebisDocument",
    "StructuredResult",
    "PipelineContext",
    "Pipeline",
]
