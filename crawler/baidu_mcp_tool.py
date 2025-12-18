import json
import os
import re
import time
from dataclasses import dataclass
import hashlib
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlparse

import requests

from .tool_base import BaseTool, ToolResult


@dataclass
class _McpToolDef:
    name: str
    input_schema: Dict[str, Any]
    description: str = ""


class BaiduAiSearchMcpTool(BaseTool):
    """
    百度千帆 AI Search MCP（streamableHttp）工具：
    - 通过 MCP JSON-RPC 调用远端 tool 做实时搜索
    - 把结果链接抓取为 HTML 文件（供后续 tools/structuring 处理）

    注意：
    - 本 tool 不把鉴权写死在代码里，只从环境变量读取 Bearer Token。
    - MCP server URL 与鉴权头可通过环境变量覆盖。
    """

    name = "baidu_ai_search_mcp"
    description = (
        "通过百度千帆 AI Search MCP 搜索实时信息，并抓取结果页面保存为 HTML。"
        "适用于中文/国内内容的通用搜索兜底。"
    )
    required_env_vars = ["BAIDU_AISEARCH_BEARER"]
    tool_kind = "general"
    capabilities = ["web_search", "search_engine", "baidu", "cn_search", "html"]

    def __init__(
        self,
        output_dir: str,
        mcp_url: Optional[str] = None,
    ):
        self.output_dir = output_dir
        self.mcp_url = mcp_url or os.environ.get("BAIDU_AISEARCH_MCP_URL", "https://qianfan.baidubce.com/v2/ai_search/mcp")

    def run(self, task: str, limit: int, tool_name: Optional[str] = None, **kwargs) -> ToolResult:
        bearer = os.environ.get("BAIDU_AISEARCH_BEARER")
        if not bearer:
            return ToolResult(name=self.name, success=False, error="缺少 BAIDU_AISEARCH_BEARER")

        os.makedirs(self.output_dir, exist_ok=True)

        try:
            tools = self._mcp_tools_list(bearer)
            chosen = self._pick_search_tool(tools, tool_name=tool_name)
            if not chosen:
                return ToolResult(
                    name=self.name,
                    success=False,
                    output_dir=self.output_dir,
                    files=[],
                    meta={"available_tools": [t.name for t in tools]},
                    error="MCP server 未暴露可用的 search 工具",
                )

            # 允许 agent 传入 lang/hl/location 等“可能存在于 schema 的字段”
            # 未在 schema 中出现的字段会被忽略，不会影响调用。
            args = self._build_args_from_schema(chosen.input_schema, task=task, limit=limit, extra=kwargs)
            raw = self._mcp_tools_call(bearer, chosen.name, args)

            ts = int(time.time())
            raw_path = os.path.join(self.output_dir, f"baidu_mcp_{ts}.json")
            with open(raw_path, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)

            urls = list(self._extract_urls(raw))
            html_files = []
            for idx, url in enumerate(urls[: int(limit)], start=1):
                try:
                    html_path = os.path.join(self.output_dir, self._safe_filename(url, idx) + ".html")
                    self._fetch_page(url, html_path)
                    html_files.append(html_path)
                except Exception:
                    continue

            files = [raw_path] + html_files
            if not html_files:
                return ToolResult(
                    name=self.name,
                    success=False,
                    output_dir=self.output_dir,
                    files=files,
                    meta={"mcp_tool": chosen.name, "args": args, "url_count": len(urls)},
                    error="MCP 返回但未抓取到任何网页（可能无可用 link 或被反爬）",
                )

            return ToolResult(
                name=self.name,
                success=True,
                output_dir=self.output_dir,
                files=files,
                meta={"mcp_tool": chosen.name, "args": args, "url_count": len(urls), "fetched": len(html_files)},
            )

        except Exception as exc:  # noqa: BLE001
            return ToolResult(
                name=self.name,
                success=False,
                output_dir=self.output_dir,
                files=[],
                error=str(exc),
                meta={"mcp_url": self.mcp_url},
            )

    # ===== MCP JSON-RPC (streamableHttp) =====
    def _mcp_request(self, bearer: str, method: str, params: Optional[dict] = None) -> dict:
        headers = {
            "Authorization": bearer if bearer.lower().startswith("bearer ") else f"Bearer {bearer}",
            "Content-Type": "application/json",
        }
        body = {"jsonrpc": "2.0", "id": int(time.time() * 1000), "method": method}
        if params is not None:
            body["params"] = params
        r = requests.post(self.mcp_url, json=body, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        if "error" in data:
            raise RuntimeError(f"MCP error: {data['error']}")
        return data.get("result", data)

    def _mcp_initialize(self, bearer: str) -> None:
        self._mcp_request(
            bearer,
            "initialize",
            {
                "clientInfo": {"name": "webis", "version": "0.1"},
                "capabilities": {},
            },
        )

    def _mcp_tools_list(self, bearer: str) -> List[_McpToolDef]:
        self._mcp_initialize(bearer)
        result = self._mcp_request(bearer, "tools/list", {})
        items = result.get("tools", result.get("result", {}).get("tools", [])) if isinstance(result, dict) else []

        tools: List[_McpToolDef] = []
        for t in items or []:
            name = t.get("name") or ""
            if not name:
                continue
            tools.append(
                _McpToolDef(
                    name=name,
                    description=t.get("description") or "",
                    input_schema=t.get("inputSchema") or {},
                )
            )
        return tools

    def _mcp_tools_call(self, bearer: str, tool_name: str, args: dict) -> dict:
        self._mcp_initialize(bearer)
        return self._mcp_request(bearer, "tools/call", {"name": tool_name, "arguments": args})

    # ===== Tool picking / argument building =====
    @staticmethod
    def _pick_search_tool(tools: List[_McpToolDef], tool_name: Optional[str]) -> Optional[_McpToolDef]:
        if tool_name:
            for t in tools:
                if t.name == tool_name:
                    return t
        # heuristic: pick a tool whose name contains "search"
        for t in tools:
            if "search" in t.name.lower():
                return t
        return tools[0] if tools else None

    @staticmethod
    def _build_args_from_schema(schema: Dict[str, Any], task: str, limit: int, extra: Optional[dict] = None) -> dict:
        """
        从 MCP tool 的 inputSchema 自动填充参数：
        - 优先满足 required 字段
        - 常见字段名：query/q/keyword/text, limit/num/top_k
        """
        props = schema.get("properties") if isinstance(schema, dict) else {}
        required = schema.get("required") if isinstance(schema, dict) else []
        if not isinstance(props, dict):
            props = {}
        if not isinstance(required, list):
            required = []

        args: Dict[str, Any] = {}
        extra = extra or {}

        def set_first(candidates: Iterable[str], value: Any):
            for k in candidates:
                if k in props:
                    args[k] = value
                    return True
            return False

        # fill required text field
        if not set_first(["query", "q", "keyword", "text", "input"], task):
            # if schema has required fields, try to set one string-required field
            for k in required:
                if k in props and isinstance(props.get(k), dict) and props[k].get("type") == "string":
                    args[k] = task
                    break

        # fill required limit field
        set_first(["limit", "num", "top_k", "k", "count"], int(limit))

        # passthrough: if extra kwarg exists in schema properties, forward it (e.g. lang/hl/gl/location)
        for k, v in extra.items():
            if k in props and k not in args:
                args[k] = v

        # ensure required fields exist (best-effort)
        for k in required:
            if k in args:
                continue
            if k in ("lang", "hl"):
                args[k] = "zh"
                continue
            if k in props and isinstance(props.get(k), dict):
                t = props[k].get("type")
                if t == "string":
                    args[k] = ""
                elif t == "integer":
                    args[k] = 0
                elif t == "number":
                    args[k] = 0
                elif t == "boolean":
                    args[k] = False
                elif t == "array":
                    args[k] = []
                elif t == "object":
                    args[k] = {}

        return args

    # ===== Result parsing / saving =====
    @staticmethod
    def _extract_urls(obj: Any) -> Iterable[str]:
        """
        尽量从 MCP 返回里提取 url/link/href。
        """
        seen = set()

        def walk(x: Any):
            if isinstance(x, dict):
                for k, v in x.items():
                    lk = str(k).lower()
                    if lk in ("url", "link", "href") and isinstance(v, str) and v.startswith(("http://", "https://")):
                        if v not in seen:
                            seen.add(v)
                            yield v
                    else:
                        yield from walk(v)
            elif isinstance(x, list):
                for it in x:
                    yield from walk(it)
            elif isinstance(x, str):
                for m in re.findall(r"https?://[^\s\"')]+", x):
                    if m not in seen:
                        seen.add(m)
                        yield m

        yield from walk(obj)

    @staticmethod
    def _safe_filename(url: str, idx: int) -> str:
        host = urlparse(url).netloc.replace(":", "_") or "site"
        h = hashlib.md5(url.encode("utf-8", errors="ignore")).hexdigest()[:8]
        return f"baidu_{idx:02d}_{host}_{h}"

    @staticmethod
    def _fetch_page(url: str, path: str) -> None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=20)
        # 某些站点不返回 charset，requests 会默认 ISO-8859-1，导致中文页面乱码（mojibake）
        if not r.encoding or r.encoding.lower() == "iso-8859-1":
            r.encoding = r.apparent_encoding
        r.raise_for_status()
        with open(path, "w", encoding="utf-8") as f:
            f.write(r.text)
