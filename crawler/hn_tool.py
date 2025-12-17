import os
import requests
from .tool_base import BaseTool, ToolResult


class HackerNewsTool(BaseTool):
    name = "hackernews"
    description = (
        "从 Hacker News 获取热门讨论链接，并抓取原网页保存为 HTML 文件。"
    )

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def run(self, task: str, limit: int) -> ToolResult:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        ).json()[:limit]

        files = []

        for i in ids:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{i}.json"
            ).json()
            url = item.get("url")
            if not url:
                continue

            html = requests.get(url, timeout=20).text
            path = os.path.join(self.output_dir, f"hn_{i}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            files.append(path)

        if not files:
            return ToolResult(self.name, False, error="HN 未抓取到页面")

        return ToolResult(self.name, True, files)
