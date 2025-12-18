import os
import hashlib
from typing import Optional

import requests

from .tool_base import BaseTool, ToolResult


class GNewsTool(BaseTool):
    name = "gnews"
    description = (
        "使用 GNews API 搜索新闻，并抓取新闻原文页面保存为 HTML 文件。"
        "适用于“新闻检索/新闻报道/时事”类任务。"
        "参数：task(查询词), limit(数量), lang(可选，en/zh/...)。"
    )
    required_env_vars = ["GNEWS_API_KEY"]
    tool_kind = "specialized"
    capabilities = ["news", "current_events"]

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.api_key = os.environ.get("GNEWS_API_KEY")

    def run(self, task: str, limit: int, lang: Optional[str] = None, **kwargs) -> ToolResult:
        if not self.api_key:
            return ToolResult(name=self.name, success=False, error="缺少 GNEWS_API_KEY")

        os.makedirs(self.output_dir, exist_ok=True)

        url = "https://gnews.io/api/v4/search"
        params = {
            "q": task,
            "lang": lang or "en",
            "max": limit,
            "token": self.api_key,
        }

        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        articles = r.json().get("articles", []) or []

        files = []
        for a in articles:
            link = a.get("url")
            if not link:
                continue

            title = (a.get("title") or "gnews").strip()
            safe = title[:60].replace("/", "_")
            h = hashlib.md5(link.encode("utf-8", errors="ignore")).hexdigest()[:8]
            html_path = os.path.join(self.output_dir, f"{safe}_{h}.html")
            self._fetch_page(link, html_path)
            files.append(html_path)

        if not files:
            return ToolResult(
                name=self.name,
                success=False,
                output_dir=self.output_dir,
                files=[],
                meta={"lang": params["lang"], "q": params["q"]},
                error="未抓取到任何新闻页面",
            )

        return ToolResult(
            name=self.name,
            success=True,
            output_dir=self.output_dir,
            files=files,
            meta={"count": len(files), "lang": params["lang"], "q": params["q"]},
        )

    def _fetch_page(self, url: str, path: str) -> None:
        r = requests.get(url, timeout=20)
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding
        r.raise_for_status()
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
