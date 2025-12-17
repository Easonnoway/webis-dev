import os
import requests
from bs4 import BeautifulSoup
from .tool_base import BaseTool, ToolResult


class GNewsTool(BaseTool):
    name = "gnews"
    description = (
        "使用 GNews API 搜索新闻，并抓取新闻原文页面保存为 HTML，"
        "同时下载页面中的图片。禁止生成 JSON 或摘要。"
    )

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.api_key = os.environ.get("GNEWS_API_KEY")

    def run(self, task: str, limit: int) -> ToolResult:
        if not self.api_key:
            return ToolResult(self.name, False, error="缺少 GNEWS_API_KEY")

        url = "https://gnews.io/api/v4/search"
        params = {
            "q": task,
            "lang": "en",
            "max": limit,
            "token": self.api_key,
        }

        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        articles = r.json().get("articles", [])

        files = []

        for a in articles:
            link = a.get("url")
            if not link:
                continue

            html_path = os.path.join(
                self.output_dir,
                a["title"][:60].replace("/", "_") + ".html"
            )
            self._fetch_page(link, html_path)
            files.append(html_path)

        if not files:
            return ToolResult(self.name, False, error="未抓取到任何新闻页面")

        return ToolResult(self.name, True, files)

    def _fetch_page(self, url: str, path: str):
        r = requests.get(url, timeout=20)
        r.raise_for_status()
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
