from __future__ import annotations

import requests
import time
from pathlib import Path

from .tool_base import BaseTool, ToolResult


class SemanticScholarTool(BaseTool):
    """
    Fetch academic papers from Semantic Scholar and save as HTML
    (Webis-consumable format).
    """

    name = "semantic_scholar"
    description = (
        "必须使用该工具从 Semantic Scholar API 获取真实学术论文。"
        "仅用于学术论文检索，禁止编造结果。"
        "返回 HTML 文件供后续 Webis pipeline 处理。"
    )

    API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"

    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run(self, task: str, limit: int = 5) -> ToolResult:
        params = {
            "query": task,
            "limit": limit,
            "fields": "title,abstract,year,authors,url,openAccessPdf",
        }

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }

        # === Step 1: query Semantic Scholar API ===
        try:
            r = requests.get(
                self.API_URL,
                params=params,
                headers=headers,
                timeout=15,
            )
            r.raise_for_status()
        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)

            if status == 429:
                return ToolResult(
                    name=self.name,
                    success=False,
                    error="Semantic Scholar API rate-limited (429). Try again later.",
                )

            return ToolResult(
                name=self.name,
                success=False,
                error=f"Semantic Scholar HTTP error: {e}",
            )

        except requests.RequestException as e:
            return ToolResult(
                name=self.name,
                success=False,
                error=f"Semantic Scholar request failed: {e}",
            )

        data = r.json()
        papers = data.get("data", [])

        if not papers:
            return ToolResult(
                name=self.name,
                success=False,
                error="Semantic Scholar returned no papers.",
            )

        # === Step 2: fetch paper pages ===
        files = []
        for idx, paper in enumerate(papers, 1):
            url = paper.get("url")
            if not url:
                continue

            html_path = self.output_dir / f"semantic_{idx}.html"

            try:
                time.sleep(1.2)  # polite crawling
                r = requests.get(url, headers=headers, timeout=15)
                r.raise_for_status()
                html_path.write_text(r.text, encoding="utf-8")
                files.append(str(html_path))
            except requests.RequestException:
                continue

        if not files:
            return ToolResult(
                name=self.name,
                success=False,
                error="Papers found but none could be fetched.",
            )

        return ToolResult(
            name=self.name,
            success=True,
            output_dir=str(self.output_dir),
            files=files,
            meta={"count": len(files)},
        )
