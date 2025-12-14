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
        # Prefer environment variable DEEPSEEK_API_KEY, fall back to provided parameter
        self.deepseek_api_key = os.environ.get("DEEPSEEK_API_KEY") or deepseek_api_key

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

    def _deepseek_enhance(self, text: str) -> str:
        if not self.deepseek_api_key:
            logger.warning("[HTMLProcessor] No DeepSeek API key provided, skipping enhancement")
            return text

        try:
            import requests

            url = "https://api.deepseek.com/v1/chat/completions"
            payload = {
                "model": "deepseek-chat",
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
                    "error": "webis-html extraction requires DeepSeek API key. Set DEEPSEEK_API_KEY or pass api_key"
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
