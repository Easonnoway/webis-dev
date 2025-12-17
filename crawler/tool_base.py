"""Common interfaces for data-source tools used by the crawler agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import os
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


def _env_vars_present(required: List[str]) -> bool:
    return all(os.environ.get(k) for k in (required or []))


class BaseTool(ABC):
    """Abstract base class for data-source tools."""

    name: str
    description: str
    # Tool 自己声明“需要哪些环境变量/参数”，由总调度 Agent 决策是否使用/如何填参。
    required_env_vars: List[str] = []
    # 工具类型：specialized（特定数据源/特定场景） vs general（通用爬虫/通用搜索引擎）
    tool_kind: str = "specialized"
    # 能力/场景标签（供总调度 Agent 匹配任务）
    capabilities: List[str] = []

    @abstractmethod
    def run(self, task: str, **kwargs) -> ToolResult:
        """Run the tool with a natural-language task."""
        raise NotImplementedError
