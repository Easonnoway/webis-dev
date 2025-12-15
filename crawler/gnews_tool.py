from __future__ import annotations

import os
import json
import time
import requests
from typing import List

from tool_base import BaseTool, ToolResult


class GNewsTool(BaseTool):
    """
    Use GNews API to search news articles by keywords.
    """

    name = "gnews_search"
    description = (
        "通过 GNews API 搜索新闻。适合获取近期新闻、技术动态、事件报道。"
        "输入应为关键词或关键词列表。"
    )

    def __init__(self, api_key: str | None = None, language: str = "zh"):
        self.api_key = api_key or os.getenv("GNEWS_API_KEY")
        if not self.api_key:
            raise RuntimeError("缺少 GNews API Key，请设置环境变量 GNEWS_API_KEY")

        self.language = language
        self.base_url = "https://gnews.io/api/v4/search"

    def run(self, task: str, limit: int = 5, **kwargs) -> ToolResult:
        """
        task: 搜索关键词，可以是一句话或用逗号分隔的多个关键词
        limit: 每个关键词返回的最大新闻条数
        """

        keywords = self._parse_keywords(task)
        timestamp = int(time.time())
        output_dir = f"gnews_outputs/{timestamp}"
        os.makedirs(output_dir, exist_ok=True)

        all_results = []

        try:
            for kw in keywords:
                articles = self._search_keyword(kw, limit)
                for art in articles:
                    art["__keyword__"] = kw
                all_results.extend(articles)

            output_file = os.path.join(output_dir, "gnews_results.json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)

            return ToolResult(
                name=self.name,
                success=True,
                output_dir=output_dir,
                files=[output_file],
                meta={
                    "keywords": keywords,
                    "total_articles": len(all_results),
                },
            )

        except Exception as e:
            return ToolResult(
                name=self.name,
                success=False,
                error=str(e),
            )

    def _parse_keywords(self, task: str) -> List[str]:
        """
        支持：
        - 单个关键词
        - 逗号 / 中文逗号 分隔
        """
        seps = [",", "，"]
        for sep in seps:
            if sep in task:
                return [k.strip() for k in task.split(sep) if k.strip()]
        return [task.strip()]

    def _search_keyword(self, keyword: str, limit: int) -> List[dict]:
        params = {
            "q": keyword,
            "lang": self.language,
            "max": limit,
            "apikey": self.api_key,
        }

        resp = requests.get(self.base_url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        return data.get("articles", [])
