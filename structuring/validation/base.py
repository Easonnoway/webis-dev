"""Base classes and registry for validation raters."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class RatingResult:
    """单次评分结果"""
    score: float  # 得分 (如 1-5)
    confidence: float = 1.0  # 置信度 (0-1)
    explanation: str = ""  # 评分理由
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外信息


class BaseRater(ABC):
    """所有评分器的抽象基类"""

    def __init__(self, llm=None):
        self.llm = llm
        self.name = self.__class__.__name__.replace('Rater', '').lower()

    @abstractmethod
    def rate(self, text: str) -> RatingResult:
        """评估文本，返回评分结果"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """返回评分器的描述"""
        pass


class RaterRegistry:
    """评分器注册表（工厂模式）"""
    _raters: Dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, rater_class):
        """注册评分器类"""
        cls._raters[name] = rater_class
        print(cls._raters)

    @classmethod
    def create_rater(cls, name: str, llm=None) -> BaseRater:
        """创建评分器实例"""
        if name not in cls._raters:
            raise ValueError(f"未知的评分器: {name}。可用: {list(cls._raters.keys())}")
        return cls._raters[name](llm)

    @classmethod
    def list_raters(cls) -> Dict[str, str]:
        """列出所有可用的评分器及其描述"""
        return {name: rater_class(None).description
                for name, rater_class in cls._raters.items()}