"""DuckDuckGo + Scrapy crawler implemented as a reusable tool."""

from __future__ import annotations

import argparse
import logging
import os
import re
import time
from typing import Dict, List, Optional
from urllib.parse import unquote, urlparse

import scrapy
from ddgs import DDGS
from scrapy.crawler import CrawlerProcess
from scrapy.pipelines.files import FilesPipeline
from scrapy.settings import Settings

if __package__ is None or not __package__:
    # Allow running as script: python crawler/ddg_scrapy_tool.py ...
    # Also handle case when imported by agent.py running as script
    import pathlib
    import sys

    parent_dir = str(pathlib.Path(__file__).resolve().parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    from tool_base import BaseTool, ToolResult  # type: ignore  # noqa: E402
else:
    from .tool_base import BaseTool, ToolResult  # type: ignore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class WebisItem(scrapy.Item):
    file_urls = scrapy.Field()
    files = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    file_type = scrapy.Field()
    download_id = scrapy.Field()
    is_file_download = scrapy.Field()
    status = scrapy.Field()


class DDGFilesPipeline(FilesPipeline):
    """Download PDF/Doc/PPT files returned by the spider."""

    TARGET_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx"}

    def get_media_requests(self, item, info):
        if item.get("is_file_download") and item.get("file_urls"):
            return scrapy.Request(url=item["file_urls"][0], meta={"item": item})
        return []

    def file_path(self, request, response=None, info=None, *, item=None):
        item = request.meta.get("item", item)

        download_id = item.get("download_id", 0)
        parsed_url = urlparse(request.url)
        filename_raw = os.path.basename(unquote(parsed_url.path)) or "downloaded_file"

        _, ext = os.path.splitext(filename_raw)
        ext = ext.lower()

        if ext not in self.TARGET_EXTS and response:
            content_type = response.headers.get(b"content-type", b"").decode("utf-8").lower()
            if "pdf" in content_type:
                ext = ".pdf"
            elif "word" in content_type:
                ext = ".docx"
            elif "ppt" in content_type:
                ext = ".pptx"

        if not ext:
            ext = ".dat"

        filename = f"{download_id}{ext}"
        return filename

    def item_completed(self, results, item, info):
        file_paths = [x["path"] for ok, x in results if ok]

        if file_paths:
            item["content"] = f"File downloaded to: {file_paths[0]}"
            item["file_type"] = os.path.splitext(file_paths[0])[1].upper()
            item["status"] = "downloaded"
        else:
            item["status"] = "download_failed"
            item["content"] = "Download failed or file not found."

        return item


class DDGScrapySpider(scrapy.Spider):
    name = "webis_ddg_tool"

    BLOCKED_DOMAINS = {"zhihu.com", "baidu.com", "tieba.baidu.com", "facebook.com"}
    TARGET_FILE_EXTS = {".pdf", ".doc", ".docx", ".ppt", ".pptx"}

    def __init__(self, keyword: str, limit: int = 5, download_dir: Optional[str] = None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not keyword:
            raise ValueError("Keyword must be provided.")

        self.keyword = keyword
        self.limit = int(limit)
        self.results_collected = 0
        self.url_history = set()
        self.download_counter = 0

        safe_keyword = re.sub(r"[^a-zA-Z0-9_-]+", "_", keyword.strip()) or "run"
        self.run_id = f"{safe_keyword}_{int(time.time())}"
        self.download_dir = download_dir or os.path.join(os.path.dirname(__file__), "outputs", self.run_id)
        os.makedirs(self.download_dir, exist_ok=True)
        logger.info("Output directory: %s", self.download_dir)

    def _is_blocked(self, url: str) -> bool:
        domain = urlparse(url).netloc.lower()
        return any(blocked in domain for blocked in self.BLOCKED_DOMAINS)

    def _get_file_ext(self, url: str) -> str:
        return os.path.splitext(urlparse(url).path)[1].lower()

    def start_requests(self):
        logger.info("Searching DuckDuckGo for: %s", self.keyword)

        file_queries = [f"{self.keyword} filetype:{ext.lstrip('.')}" for ext in self.TARGET_FILE_EXTS]
        all_queries = file_queries + [self.keyword.strip()]

        all_urls: List[Dict[str, str]] = []
        with DDGS() as ddgs:
            for query in all_queries:
                if self.results_collected >= self.limit:
                    break

                try:
                    results_to_fetch = self.limit - self.results_collected + 2
                    search_gen = ddgs.text(query, max_results=results_to_fetch, safesearch="moderate")

                    for r in search_gen:
                        url = r.get("href")
                        title = r.get("title")
                        if not url or self._is_blocked(url):
                            continue

                        if url not in self.url_history:
                            all_urls.append({"url": url, "title": title})
                            self.url_history.add(url)
                            self.results_collected += 1

                        if self.results_collected >= self.limit:
                            break

                    time.sleep(1)
                except Exception as exc:  # noqa: BLE001
                    self.logger.error("Error searching for %s: %s", query, exc)

        logger.info("Found %s target URLs. Starting Scrapy requests...", len(all_urls))

        for info in all_urls:
            url = info["url"]
            title = info["title"]
            ext = self._get_file_ext(url)

            self.download_counter += 1
            current_id = self.download_counter

            meta = {"title": title, "original_url": url, "download_id": current_id}

            if ext in self.TARGET_FILE_EXTS:
                yield WebisItem(
                    file_urls=[url],
                    title=title,
                    url=url,
                    is_file_download=True,
                    download_id=current_id,
                )
            else:
                yield scrapy.Request(url=url, callback=self.parse_html, meta=meta)

    def parse_html(self, response):
        item = WebisItem()
        item["url"] = response.meta.get("original_url")
        item["title"] = response.meta.get("title", response.css("title::text").get())
        item["file_type"] = ".HTML"
        item["status"] = "success"
        item["download_id"] = response.meta.get("download_id")
        item["is_file_download"] = False

        self._save_raw_html(response.text, item)
        item["content"] = "Raw HTML saved to file."
        yield item

    def _save_raw_html(self, response_text: str, item: WebisItem):
        download_id = item.get("download_id", 0)
        base_filename = f"{download_id}.html"
        filepath = os.path.join(self.download_dir, base_filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(response_text)
            self.logger.info("Saved HTML content to %s", os.path.basename(filepath))
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Failed to save raw HTML for %s: %s", item["url"], exc)
            item["status"] = "save_failed"


class DuckDuckGoScrapyTool(BaseTool):
    """Wraps the DDG + Scrapy spider into a callable tool."""

    name = "duckduckgo_scrapy"
    description = "Use DuckDuckGo + Scrapy to fetch documents or HTML pages for a keyword."
    required_env_vars = []
    tool_kind = "general"
    capabilities = ["web_search", "generic_crawl", "download_files", "html"]

    def __init__(self, output_root: Optional[str] = None):
        self.output_root = output_root or os.path.join(os.path.dirname(__file__), "outputs")
        os.makedirs(self.output_root, exist_ok=True)

    def run(
        self,
        task: str,
        limit: int = 5,
        concurrency: int = 8,
        download_delay: float = 0.5,
        output_dir: Optional[str] = None,
        **kwargs,
    ) -> ToolResult:
        keyword = task.strip()
        if not keyword:
            return ToolResult(name=self.name, success=False, error="Task/keyword is empty.")

        run_dir = output_dir or self._build_run_dir(keyword)
        os.makedirs(run_dir, exist_ok=True)

        settings = self._build_scrapy_settings(run_dir, concurrency, download_delay)
        process = CrawlerProcess(settings)

        logger.info(
            "Starting DDG Scrapy tool run. keyword=%s limit=%s output_dir=%s", keyword, limit, run_dir
        )

        try:
            process.crawl(DDGScrapySpider, keyword=keyword, limit=limit, download_dir=run_dir)
            process.start()
        except Exception as exc:  # noqa: BLE001
            logger.error("Scrapy run failed: %s", exc)
            return ToolResult(
                name=self.name,
                success=False,
                output_dir=run_dir,
                files=[],
                meta={"keyword": keyword},
                error=str(exc),
            )

        files = self._collect_files(run_dir)
        meta = {"keyword": keyword, "limit": limit, "run_dir": run_dir}
        return ToolResult(name=self.name, success=True, output_dir=run_dir, files=files, meta=meta)

    def _build_run_dir(self, keyword: str) -> str:
        safe_keyword = re.sub(r"[^a-zA-Z0-9_-]+", "_", keyword.strip()) or "run"
        run_id = f"{safe_keyword}_{int(time.time())}"
        return os.path.join(self.output_root, run_id)

    def _build_scrapy_settings(self, output_dir: str, concurrency: int, download_delay: float) -> Settings:
        settings = Settings()
        settings.set("ITEM_PIPELINES", {f"{__name__}.DDGFilesPipeline": 1}, priority="cmdline")
        settings.set("FILES_STORE", output_dir, priority="cmdline")
        settings.set("CONCURRENT_REQUESTS", concurrency, priority="cmdline")
        settings.set("DOWNLOAD_DELAY", download_delay, priority="cmdline")
        settings.set("ROBOTSTXT_OBEY", False, priority="cmdline")
        settings.set("LOG_ENABLED", False, priority="cmdline")
        return settings

    def _collect_files(self, output_dir: str) -> List[str]:
        root_files = []
        pipeline_files = []

        try:
            root_files = [
                os.path.join(output_dir, name)
                for name in os.listdir(output_dir)
                if name.split(".")[0].isdigit()
            ]

            pipeline_dir = os.path.join(output_dir, "full")
            if os.path.isdir(pipeline_dir):
                pipeline_files = [
                    os.path.join(pipeline_dir, name)
                    for name in os.listdir(pipeline_dir)
                    if name.split(".")[0].isdigit()
                ]
        except FileNotFoundError:
            logger.warning("Output directory missing, cannot collect files: %s", output_dir)

        all_files = root_files + pipeline_files

        def sort_key(fpath: str) -> int:
            try:
                base_name = os.path.basename(fpath)
                return int(base_name.split(".")[0])
            except ValueError:
                return 0

        return sorted(all_files, key=sort_key)


def cli():
    parser = argparse.ArgumentParser(description="Run the DuckDuckGo Scrapy tool directly.")
    parser.add_argument("keyword", help="Keyword to search for")
    parser.add_argument("--limit", type=int, default=5, help="Max number of results to crawl")
    parser.add_argument("--output", type=str, default=None, help="Optional output directory")
    args = parser.parse_args()

    tool = DuckDuckGoScrapyTool()
    result = tool.run(task=args.keyword, limit=args.limit, output_dir=args.output)

    if result.success:
        print(f"✓ Crawl finished. Output dir: {result.output_dir}")
        print("Files:")
        for f in result.files:
            print(f" - {f}")
    else:
        print(f"✗ Crawl failed: {result.error}")


if __name__ == "__main__":
    cli()
