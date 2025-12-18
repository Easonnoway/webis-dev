import json
import os
import re
import time
from typing import Optional
import hashlib
from urllib.parse import urlparse

import requests

from .tool_base import BaseTool, ToolResult


class SerpApiSearchTool(BaseTool):
    """
    SerpApi 搜索抓取工具：
    - 调用 SerpApi Search API 获取搜索结果
    - 把 SERP 返回的链接抓取为 HTML 文件（供 tools/structuring 后续处理）
    """

    name = "serpapi"
    description = (
        "使用 SerpApi Search API 进行搜索，并抓取结果页面保存。"
        "适用于“泛搜索/Google 搜索/需要更多兜底来源”的任务。"
        "参数：task(查询词), limit(数量), engine(默认 google), hl/gl/location(可选)。"
    )
    required_env_vars = ["SERPAPI_API_KEY"]
    tool_kind = "general"
    capabilities = ["web_search", "search_engine", "google", "generic_crawl", "html"]

    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.api_key = os.environ.get("SERPAPI_API_KEY")

    def run(
        self,
        task: str,
        limit: int,
        engine: str = "google",
        hl: Optional[str] = None,
        gl: Optional[str] = None,
        location: Optional[str] = None,
        safe: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        if not self.api_key:
            return ToolResult(name=self.name, success=False, error="缺少 SERPAPI_API_KEY")

        os.makedirs(self.output_dir, exist_ok=True)

        params = {
            "engine": engine,
            "q": task,
            "api_key": self.api_key,
            "num": int(limit),
        }
        if hl:
            params["hl"] = hl
        if gl:
            params["gl"] = gl
        if location:
            params["location"] = location
        if safe:
            params["safe"] = safe

        r = requests.get("https://serpapi.com/search", params=params, timeout=30)
        r.raise_for_status()
        data = r.json()

        ts = int(time.time())
        resp_path = os.path.join(self.output_dir, f"serpapi_{ts}.json")
        with open(resp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        organic = data.get("organic_results", []) or []
        files = [resp_path]

        fetched = 0
        for item in organic:
            if fetched >= int(limit):
                break
            link = item.get("link")
            if not link:
                continue
            title = (item.get("title") or f"result_{fetched+1}").strip()
            html_path = os.path.join(self.output_dir, self._safe_filename(title, link, fetched + 1) + ".html")
            try:
                self._fetch_page(link, html_path)
                files.append(html_path)
                fetched += 1
            except Exception:
                continue

        if fetched == 0:
            return ToolResult(
                name=self.name,
                success=False,
                output_dir=self.output_dir,
                files=files,
                meta={"engine": engine, "q": task, "resp_json": resp_path},
                error="SerpApi 返回了结果但未成功抓取任何页面",
            )

        return ToolResult(
            name=self.name,
            success=True,
            output_dir=self.output_dir,
            files=files,
            meta={"engine": engine, "q": task, "resp_json": resp_path, "fetched_html": fetched},
        )

    def _fetch_page(self, url: str, path: str) -> None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=20)
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding
        r.raise_for_status()
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)

    @staticmethod
    def _safe_filename(title: str, url: str, idx: int) -> str:
        host = urlparse(url).netloc.replace(":", "_") or "site"
        base = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff._-]+", "_", title)[:80].strip("_")
        if not base:
            base = f"result_{idx}"
        h = hashlib.md5(url.encode("utf-8", errors="ignore")).hexdigest()[:8]
        return f"serp_{idx:02d}_{host}_{h}_{base}"
