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


class SemanticScholarTool(BaseTool):
    name = "academic_search"
    description = (
        "搜索学术论文（Semantic Scholar）。适合查找论文、研究进展、引用情况。"
    )

    def __init__(self):
        self.base_url = "https://api.semanticscholar.org/graph/v1/paper/search"

    def run(self, task: str, limit: int = 5, **kwargs) -> ToolResult:
        ts = int(time.time())
        output_dir = f"academic_outputs/{ts}"
        os.makedirs(output_dir, exist_ok=True)

        params = {
            "query": task,
            "limit": limit,
            "fields": "title,abstract,authors,year,citationCount,venue,url",
        }

        try:
            r = requests.get(self.base_url, params=params, timeout=20)
            r.raise_for_status()
            papers = r.json().get("data", [])

            out = os.path.join(output_dir, "semantic_scholar.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(papers, f, ensure_ascii=False, indent=2)

            return ToolResult(
                name=self.name,
                success=True,
                output_dir=output_dir,
                files=[out],
                meta={"query": task, "count": len(papers)},
            )

        except Exception as e:
            return ToolResult(name=self.name, success=False, error=str(e))
