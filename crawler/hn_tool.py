from __future__ import annotations

import os
import json
import time
import requests
import sys
import pathlib

if not __package__:
    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    from tool_base import BaseTool, ToolResult
else:
    from .tool_base import BaseTool, ToolResult


class HackerNewsTool(BaseTool):
    """
    Community discussion search via Hacker News (Algolia API).
    """

    name = "community_search"
    description = (
        "搜索 Hacker News 社区讨论。适合获取工程师观点、技术趋势和实践经验。"
    )

    def __init__(self):
        self.search_url = "https://hn.algolia.com/api/v1/search"

    def run(self, task: str, limit: int = 5, **kwargs) -> ToolResult:
        ts = int(time.time())
        output_dir = f"community_outputs/{ts}"
        os.makedirs(output_dir, exist_ok=True)

        params = {
            "query": task,
            "tags": "story",
            "hitsPerPage": limit,
        }

        try:
            r = requests.get(self.search_url, params=params, timeout=15)
            r.raise_for_status()
            hits = r.json().get("hits", [])

            out = os.path.join(output_dir, "hackernews.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(hits, f, ensure_ascii=False, indent=2)

            return ToolResult(
                name=self.name,
                success=True,
                output_dir=output_dir,
                files=[out],
                meta={"query": task, "count": len(hits)},
            )

        except Exception as e:
            return ToolResult(
                name=self.name,
                success=False,
                error=str(e),
            )
