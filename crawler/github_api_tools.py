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


class GitHubSearchTool(BaseTool):
    name = "code_search"
    description = (
        "搜索 GitHub 开源仓库。适合查找真实代码实现和工程项目。"
    )

    def __init__(self, token: str | None = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.base_url = "https://api.github.com/search/repositories"

    def run(self, task: str, limit: int = 5, **kwargs) -> ToolResult:
        ts = int(time.time())
        output_dir = f"code_outputs/{ts}"
        os.makedirs(output_dir, exist_ok=True)

        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        params = {
            "q": task,
            "sort": "stars",
            "order": "desc",
            "per_page": limit,
        }

        try:
            r = requests.get(
                self.base_url, headers=headers, params=params, timeout=20
            )
            r.raise_for_status()
            repos = r.json().get("items", [])

            out = os.path.join(output_dir, "github_repos.json")
            with open(out, "w", encoding="utf-8") as f:
                json.dump(repos, f, ensure_ascii=False, indent=2)

            return ToolResult(
                name=self.name,
                success=True,
                output_dir=output_dir,
                files=[out],
                meta={"query": task, "count": len(repos)},
            )

        except Exception as e:
            return ToolResult(name=self.name, success=False, error=str(e))
