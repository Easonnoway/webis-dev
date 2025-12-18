#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML Processor (based on webis-html library + optional DeepSeek enhancement)
Dependency: pip install webis-html
"""

import logging
import os
import tempfile
import re
from typing import Dict, Union, Set, Optional

from .base_processor import BaseFileProcessor

logger = logging.getLogger(__name__)

try:
    import webis_html
except ImportError:
    webis_html = None


class HTMLProcessor(BaseFileProcessor):
    """HTML file processor - extracts main content using webis-html + optional DeepSeek cleanup"""

    def __init__(self, deepseek_api_key: Optional[str] = None):
        super().__init__()
        self.supported_extensions = {".html", ".htm"}
        # Prefer SILICONFLOW_API_KEY, fall back to DEEPSEEK_API_KEY / provided parameter (compat)
        self.deepseek_api_key = (
            os.environ.get("SILICONFLOW_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or deepseek_api_key
        )
        self._ensure_webis_html_env()

    def _ensure_webis_html_env(self) -> None:
        """
        webis-html 内部默认读取环境变量：
        - LLM_PREDICTOR_API_KEY 或 DEEPSEEK_API_KEY
        - LLM_PREDICTOR_API_URL / LLM_PREDICTOR_MODEL

        为了与本项目统一（SILICONFLOW_API_KEY + DeepSeek-V3.2），这里做一次环境变量映射。
        """
        if not self.deepseek_api_key:
            return

        # webis-html 不认识 SILICONFLOW_API_KEY，这里把它映射到它读取的变量名上，
        # 保证你只需要配置 SILICONFLOW_API_KEY 一处即可。
        os.environ.setdefault("LLM_PREDICTOR_API_KEY", self.deepseek_api_key)
        os.environ.setdefault("LLM_PREDICTOR_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
        os.environ.setdefault("LLM_PREDICTOR_MODEL", "deepseek-ai/DeepSeek-V3.2")

        try:
            from webis_html.core import llm_predictor  # type: ignore

            if getattr(llm_predictor, "_API_KEY_CACHE", None) is None:
                return
            llm_predictor._API_KEY_CACHE = None  # type: ignore[attr-defined]
        except Exception:
            return

    def get_processor_name(self) -> str:
        return "HTMLProcessor"

    def get_supported_extensions(self) -> Set[str]:
        return self.supported_extensions

    def _basic_noise_reduction(self, text: str) -> str:
        # Normalize line breaks and whitespace
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)

        # Remove empty lines and very short lines
        lines = [line.strip() for line in text.split('\n')]
        cleaned_lines = [line for line in lines if len(line) >= 3]

        return '\n\n'.join(cleaned_lines).strip()

    @staticmethod
    def _maybe_fix_mojibake(text: str) -> str:
        """
        修复常见“UTF-8 被当成 Latin-1 解码”导致的中文乱码（如 'æ¸…å�Ž'）。
        仅在修复后中文字符显著增加时才应用，避免误伤正常内容。
        """
        if not text:
            return text

        def cjk_count(s: str) -> int:
            return sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")

        before = cjk_count(text)
        # 典型 mojibake 会包含大量 'Ã' 'Â' 'å' 'æ' 等字符
        marker = sum(text.count(x) for x in ("Ã", "Â", "æ", "å", "ç", "é"))
        if marker < 20:
            return text

        try:
            fixed = text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            return text

        after = cjk_count(fixed)
        return fixed if after >= before + 10 else text

    def _deepseek_enhance(self, text: str) -> str:
        if not self.deepseek_api_key:
            logger.warning("[HTMLProcessor] No DeepSeek API key provided, skipping enhancement")
            return text

        try:
            import requests

            url = "https://api.siliconflow.cn/v1/chat/completions"
            payload = {
                "model": "deepseek-ai/DeepSeek-V3.2",
                "messages": [
                    {"role": "system", "content": "Fix typos, garbled text, punctuation and formatting errors in the text. Only correct, do not add or remove content."},
                    {"role": "user", "content": text}
                ],
                "temperature": 0.3,
                "max_tokens": 2048
            }
            headers = {
                "Authorization": f"Bearer {self.deepseek_api_key}",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()
            result = response.json()
            enhanced_text = result['choices'][0]['message']['content'].strip()

            logger.info("[HTMLProcessor] DeepSeek enhancement successful")
            return enhanced_text

        except ImportError:
            logger.error("[HTMLProcessor] Missing requests library. Install with: pip install requests")
            return text
        except Exception as e:
            logger.error(f"[HTMLProcessor] DeepSeek enhancement failed: {str(e)}")
            return text

    def extract_text(self, file_path: str, use_deepseek: bool = False) -> Dict[str, Union[str, bool]]:
        if not os.path.exists(file_path):
            return {"success": False, "text": "", "error": f"File not found: {file_path}"}

        if webis_html is None:
            return {
                "success": False,
                "text": "",
                "error": "webis_html module not installed. Run: pip install webis-html"
            }

        try:
            if not self.deepseek_api_key:
                return {
                    "success": False,
                    "text": "",
                    "error": "webis-html extraction requires SiliconFlow API key. Set SILICONFLOW_API_KEY (or DEEPSEEK_API_KEY for compatibility)"
                }

            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            with tempfile.TemporaryDirectory() as temp_output_dir:
                result = webis_html.extract_from_html(
                    html_content=html_content,
                    api_key=self.deepseek_api_key,
                    output_dir=temp_output_dir
                )

                if not result.get("success", False):
                    return {"success": False, "text": "", "error": f"webis-html extraction failed: {result.get('error', 'Unknown error')}"}

                results = result.get("results", [])
                if not results:
                    return {"success": False, "text": "", "error": "No main content extracted"}

                text_parts = [item.get("content", "").strip() for item in results if item.get("content")]
                raw_text = "\n\n".join(text_parts)

                # 先修复常见编码导致的乱码，再做规则清理
                raw_text = self._maybe_fix_mojibake(raw_text)
                cleaned_text = self._basic_noise_reduction(raw_text)

                if use_deepseek:
                    cleaned_text = self._deepseek_enhance(cleaned_text)

                logger.info(
                    f"[HTMLProcessor] Processed {file_path}, segments: {len(results)}, final length: {len(cleaned_text)}"
                )

                return {
                    "success": True,
                    "text": cleaned_text,
                    "error": "",
                    "meta": {
                        "segment_count": len(results),
                        "raw_text_length": len(raw_text)
                    }
                }

        except Exception as e:
            logger.error(f"[HTMLProcessor] Processing failed {file_path}: {str(e)}")
            return {"success": False, "text": "", "error": f"Exception: {str(e)}"}
