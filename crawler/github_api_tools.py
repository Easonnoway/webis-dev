import os
import requests
from .tool_base import BaseTool, ToolResult


class GitHubSearchTool(BaseTool):
    name = "github"
    description = (
        "使用 GitHub API 搜索代码仓库，并保存 README 或仓库主页为 HTML/MD 文件。"
    )
    required_env_vars = []
    tool_kind = "specialized"
    capabilities = ["github", "code", "repo", "readme"]

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def run(self, task: str, limit: int) -> ToolResult:
        os.makedirs(self.output_dir, exist_ok=True)
        url = "https://api.github.com/search/repositories"
        r = requests.get(url, params={"q": task, "per_page": limit}, timeout=20)
        r.raise_for_status()
        items = r.json().get("items", [])

        files = []

        for repo in items:
            html_url = repo["html_url"]
            path = os.path.join(
                self.output_dir, repo["name"][:50] + ".html"
            )
            page = requests.get(html_url, timeout=20)
            if not page.encoding or page.encoding.lower() == "iso-8859-1":
                page.encoding = page.apparent_encoding
            with open(path, "w", encoding="utf-8") as f:
                f.write(page.text)
            files.append(path)

        if not files:
            return ToolResult(self.name, False, error="未获取任何 GitHub 页面")

        return ToolResult(
            name=self.name,
            success=True,
            output_dir=self.output_dir,
            files=files,
            meta={"count": len(files)},
        )
