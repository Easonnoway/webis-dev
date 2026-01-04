"""
Baidu AI Search Source Plugin for Webis.
"""

import logging
import os
import json
import time
from typing import Iterator, Optional, Dict, Any, List

import requests

from webis.core.plugin import SourcePlugin
from webis.core.schema import WebisDocument, DocumentType, DocumentMetadata, PipelineContext

logger = logging.getLogger(__name__)


class BaiduSearchPlugin(SourcePlugin):
    """
    Search using Baidu Qianfan AI Search MCP.
    """
    
    name = "baidu_search"
    description = "Search using Baidu Qianfan AI Search"
    required_env_vars = ["BAIDU_AISEARCH_BEARER"]
    
    def __init__(self, config: Optional[dict] = None):
        super().__init__(config)
        self.mcp_url = self.config.get(
            "mcp_url", 
            os.environ.get("BAIDU_AISEARCH_MCP_URL", "https://qianfan.baidubce.com/v2/ai_search/mcp")
        )

    def fetch(
        self, 
        query: str, 
        limit: int = 10, 
        context: Optional[PipelineContext] = None,
        **kwargs
    ) -> Iterator[WebisDocument]:
        bearer = os.environ.get("BAIDU_AISEARCH_BEARER")
        if not bearer:
            logger.error("Missing BAIDU_AISEARCH_BEARER")
            return

        # 1. List tools
        try:
            tools = self._mcp_tools_list(bearer)
            if not tools:
                logger.warning("No tools available from Baidu MCP")
                return
                
            # 2. Pick search tool (simplified logic: pick first 'search' tool)
            chosen_tool = None
            for tool in tools:
                if "search" in tool["name"].lower():
                    chosen_tool = tool
                    break
            
            if not chosen_tool:
                chosen_tool = tools[0]
                
            # 3. Call tool
            args = {"query": query} # Simplified arg construction
            raw_response = self._mcp_tools_call(bearer, chosen_tool["name"], args)
            
            # 4. Extract URLs and yield documents
            # The raw response structure depends on the specific MCP tool
            # Assuming it returns a list of results or a text with links
            
            # For now, let's try to extract URLs from the raw response
            # This logic is adapted from the original tool but simplified
            urls = self._extract_urls(raw_response)
            
            for i, url in enumerate(urls):
                if i >= limit:
                    break
                    
                yield WebisDocument(
                    content="", # Content to be fetched by processor
                    doc_type=DocumentType.HTML,
                    meta=DocumentMetadata(
                        url=url,
                        source_plugin=self.name,
                        title=f"Baidu Result {i+1}" # Placeholder
                    )
                )
                
        except Exception as e:
            logger.error(f"Baidu search failed: {e}")

    def _mcp_tools_list(self, bearer: str) -> List[Dict[str, Any]]:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {bearer}"}
        payload = {"jsonrpc": "2.0", "method": "tools/list", "id": 1}
        resp = requests.post(self.mcp_url, headers=headers, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return data.get("result", {}).get("tools", [])

    def _mcp_tools_call(self, bearer: str, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {bearer}"}
        payload = {
            "jsonrpc": "2.0", 
            "method": "tools/call", 
            "id": 1,
            "params": {"name": tool_name, "arguments": args}
        }
        resp = requests.post(self.mcp_url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json().get("result", {})

    def _extract_urls(self, data: Any) -> List[str]:
        # Simple recursive URL extractor
        urls = []
        if isinstance(data, str):
            # Simple regex for http/https urls
            import re
            found = re.findall(r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[/\w\.-]*', data)
            urls.extend(found)
        elif isinstance(data, list):
            for item in data:
                urls.extend(self._extract_urls(item))
        elif isinstance(data, dict):
            for v in data.values():
                urls.extend(self._extract_urls(v))
        return list(set(urls)) # Deduplicate
