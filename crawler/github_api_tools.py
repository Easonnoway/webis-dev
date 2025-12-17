import os
import requests
from .tool_base import BaseTool, ToolResult


class GitHubSearchTool(BaseTool):
    name = "github"
    description = (
        "使用 GitHub API 搜索代码仓库，并保存 README 或仓库主页为 HTML/MD 文件。"
    )

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def run(self, task: str, limit: int) -> ToolResult:
        url = "https://api.github.com/search/repositories"
        r = requests.get(url, params={"q": task, "per_page": limit})
        r.raise_for_status()
        items = r.json().get("items", [])

        files = []

        for repo in items:
            html_url = repo["html_url"]
            path = os.path.join(
                self.output_dir, repo["name"][:50] + ".html"
            )
            page = requests.get(html_url)
            with open(path, "w", encoding="utf-8") as f:
                f.write(page.text)
            files.append(path)

        if not files:
            return ToolResult(self.name, False, error="未获取任何 GitHub 页面")

        return ToolResult(self.name, True, files)
