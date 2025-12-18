import os
import requests
from .tool_base import BaseTool, ToolResult


class HackerNewsTool(BaseTool):
    name = "hackernews"
    description = (
        "从 Hacker News 获取热门讨论链接，并抓取原网页保存为 HTML 文件。"
    )
    required_env_vars = []
    tool_kind = "specialized"
    capabilities = ["news", "tech_news", "hackernews"]

    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def run(self, task: str, limit: int) -> ToolResult:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json",
            timeout=20,
        ).json()[:limit]

        files = []

        for i in ids:
            item = requests.get(
                f"https://hacker-news.firebaseio.com/v0/item/{i}.json",
                timeout=20,
            ).json()
            url = item.get("url")
            if not url:
                continue

            r = requests.get(url, timeout=20)
            if not r.encoding or r.encoding.lower() == "iso-8859-1":
                r.encoding = r.apparent_encoding
            html = r.text
            path = os.path.join(self.output_dir, f"hn_{i}.html")
            with open(path, "w", encoding="utf-8") as f:
                f.write(html)
            files.append(path)

        if not files:
            return ToolResult(self.name, False, error="HN 未抓取到页面")

        return ToolResult(
            name=self.name,
            success=True,
            output_dir=self.output_dir,
            files=files,
            meta={"count": len(files)},
        )
