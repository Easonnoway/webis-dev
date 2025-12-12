"""Common interfaces for data-source tools used by the crawler agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ToolResult:
    """Standard result returned by all tools."""

    name: str
    success: bool
    output_dir: Optional[str] = None
    files: List[str] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class BaseTool(ABC):
    """Abstract base class for data-source tools."""

    name: str
    description: str

    @abstractmethod
    def run(self, task: str, **kwargs) -> ToolResult:
        """Run the tool with a natural-language task."""
        raise NotImplementedError
