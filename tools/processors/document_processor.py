#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML Processor with pluggable text processors
"""

from typing import Dict, Union, Set, Optional
from .base_processor import BaseFileProcessor
from .text_processors import BaseTextProcessor, DeepSeekTextProcessor, NullTextProcessor
import os
import tempfile

try:
    import webis_html
except ImportError:
    webis_html = None


class HTMLProcessor(BaseFileProcessor):
    """HTML File Processor with pluggable text processing"""

    def __init__(self, text_processor: Optional[BaseTextProcessor] = None, api_key: str = None):
        super().__init__()
        self.supported_extensions = {".html", ".htm"}
        self.api_key = os.environ.get("DEEPSEEK_API_KEY") or api_key
        # 注入文本处理器，默认使用DeepSeek
        self.text_processor = text_processor or DeepSeekTextProcessor(api_key=self.api_key)

    def get_processor_name(self) -> str:
        return "HTMLProcessor"

    def get_supported_extensions(self) -> Set[str]:
        return self.supported_extensions

    def extract_text(self, file_path: str) -> Dict[str, Union[str, bool]]:
        if not os.path.exists(file_path):
            return {"success": False, "text": "", "error": f"File not found: {file_path}"}

        if webis_html is None:
            return {
                "success": False,
                "text": "",
                "error": "webis_html module not installed. Please run: pip install webis-html"
            }

        try:
            # 确保API密钥可用
            if not self.api_key:
                return {
                    "success": False,
                    "text": "",
                    "error": (
                        "DeepSeek API key not detected (DEEPSEEK_API_KEY environment variable not set, "
                        "and not provided in constructor)."
                    ),
                }

            # 读取HTML内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            # 使用webis_html提取原始文本
            with tempfile.TemporaryDirectory() as temp_output_dir:
                result = webis_html.extract_from_html(
                    html_content=html_content,
                    api_key=self.api_key,
                    output_dir=temp_output_dir
                )

                if not result.get("success", False):
                    error_msg = result.get("error", "Unknown error")
                    return {"success": False, "text": "", "error": f"Extraction failed: {error_msg}"}

                # 合并提取结果
                results = result.get("results", [])
                if not results:
                    return {"success": False, "text": "", "error": "No content extracted"}

                text_parts = [item.get("content", "") for item in results if item.get("content", "")]
                raw_text = "\n\n".join(text_parts)

            # HTML专用处理提示词
            html_task_prompt = """请对以下HTML提取文本进行优化，要求：
1. 去除HTML标签残留、脚本样式内容
2. 保留网页核心内容：文章、标题、列表
3. 修复格式错乱，优化阅读体验"""

            # 调用插拔式文本处理器
            text = self.text_processor.process(raw_text, html_task_prompt)

            return {
                "success": True,
                "text": text,
                "error": "",
                "meta": {
                    "output_dir": result.get("output_dir", ""),
                    "file_count": len(results)
                }
            }

        except Exception as e:
            return {"success": False, "text": "", "error": f"Processing failed: {str(e)}"}
