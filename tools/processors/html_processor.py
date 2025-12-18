#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML Processor (based on webis-html library + pluggable text processor)
Dependency: pip install webis-html
"""

import logging
import os
import tempfile
import re
from typing import Dict, Union, Set, Optional

from .base_processor import BaseFileProcessor
# 导入可插拔文本处理器接口
from .text_processors import BaseTextProcessor, DeepSeekTextProcessor, NullTextProcessor

logger = logging.getLogger(__name__)

try:
    import webis_html
except ImportError:
    webis_html = None


class HTMLProcessor(BaseFileProcessor):
    """HTML file processor - extracts main content using webis-html + pluggable text processor"""

    def __init__(self, text_processor: Optional[BaseTextProcessor] = None, deepseek_api_key: Optional[str] = None):
        super().__init__()
        self.supported_extensions = {".html", ".htm"}

        # 1. 兼容原有 API Key 逻辑（优先 SILICONFLOW_API_KEY）
        self.api_key = (
                os.environ.get("SILICONFLOW_API_KEY") or os.environ.get("DEEPSEEK_API_KEY") or deepseek_api_key
        )

        # 2. 注入可插拔文本处理器（默认使用 DeepSeek 实现）
        if text_processor:
            self.text_processor = text_processor
        else:
            # 初始化默认的 DeepSeek 文本处理器
            self.text_processor = DeepSeekTextProcessor(api_key=self.api_key)

        # 3. 保证 webis-html 内部环境变量配置
        self._ensure_webis_html_env()

    def _ensure_webis_html_env(self) -> None:
        """
        webis-html 内部默认读取环境变量：
        - LLM_PREDICTOR_API_KEY 或 DEEPSEEK_API_KEY
        - LLM_PREDICTOR_API_URL / LLM_PREDICTOR_MODEL

        为了与本项目统一（SILICONFLOW_API_KEY + DeepSeek-V3.2），这里做一次环境变量映射。
        """
        if not self.api_key:
            return

        # webis-html 不认识 SILICONFLOW_API_KEY，映射到它读取的变量名
        os.environ.setdefault("LLM_PREDICTOR_API_KEY", self.api_key)
        os.environ.setdefault("LLM_PREDICTOR_API_URL", "https://api.siliconflow.cn/v1/chat/completions")
        os.environ.setdefault("LLM_PREDICTOR_MODEL", "deepseek-ai/DeepSeek-V3.2")

        try:
            from webis_html.core import llm_predictor  # type: ignore
            # 清空 webis-html 的 API Key 缓存，确保环境变量生效
            if getattr(llm_predictor, "_API_KEY_CACHE", None) is not None:
                llm_predictor._API_KEY_CACHE = None  # type: ignore[attr-defined]
        except Exception:
            return

    def _basic_noise_reduction(self, text: str) -> str:
        """基础规则清洗（保留原有逻辑）"""
        # 归一化换行符和空白符
        text = re.sub(r'\r\n|\r|\n', '\n', text)
        text = re.sub(r'\s+', ' ', text)

        # 移除空行和极短行
        lines = [line.strip() for line in text.split('\n')]
        cleaned_lines = [line for line in lines if len(line) >= 3]

        return '\n\n'.join(cleaned_lines).strip()

    @staticmethod
    def _maybe_fix_mojibake(text: str) -> str:
        """修复常见编码乱码（保留原有逻辑）"""
        if not text:
            return text

        def cjk_count(s: str) -> int:
            return sum(1 for ch in s if "\u4e00" <= ch <= "\u9fff")

        before = cjk_count(text)
        # 典型 mojibake 特征字符计数
        marker = sum(text.count(x) for x in ("Ã", "Â", "æ", "å", "ç", "é"))
        if marker < 20:
            return text

        try:
            fixed = text.encode("latin-1", errors="ignore").decode("utf-8", errors="ignore")
        except Exception:
            return text

        after = cjk_count(fixed)
        return fixed if after >= before + 10 else text

    def get_processor_name(self) -> str:
        return "HTMLProcessor"

    def get_supported_extensions(self) -> Set[str]:
        return self.supported_extensions

    def extract_text(self, file_path: str, use_text_processor: bool = True) -> Dict[str, Union[str, bool]]:
        """
        提取 HTML 文本（webis-html + 基础清洗 + 可插拔文本处理器增强）
        :param file_path: HTML 文件路径
        :param use_text_processor: 是否启用文本处理器（False 则使用 Null 处理器）
        """
        if not os.path.exists(file_path):
            return {"success": False, "text": "", "error": f"File not found: {file_path}"}

        if webis_html is None:
            return {
                "success": False,
                "text": "",
                "error": "webis_html module not installed. Run: pip install webis-html"
            }

        try:
            # 校验 API Key（webis-html 提取必须依赖）
            if not self.api_key:
                return {
                    "success": False,
                    "text": "",
                    "error": "webis-html extraction requires SiliconFlow API key. Set SILICONFLOW_API_KEY (or DEEPSEEK_API_KEY for compatibility)"
                }

            # 读取 HTML 文件内容
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()

            # 使用 webis-html 提取核心内容
            with tempfile.TemporaryDirectory() as temp_output_dir:
                result = webis_html.extract_from_html(
                    html_content=html_content,
                    api_key=self.api_key,
                    output_dir=temp_output_dir
                )

                if not result.get("success", False):
                    return {"success": False, "text": "",
                            "error": f"webis-html extraction failed: {result.get('error', 'Unknown error')}"}

                results = result.get("results", [])
                if not results:
                    return {"success": False, "text": "", "error": "No main content extracted"}

                # 合并提取的文本片段
                text_parts = [item.get("content", "").strip() for item in results if item.get("content")]
                raw_text = "\n\n".join(text_parts)

                # 步骤1：修复编码乱码（原有逻辑）
                raw_text = self._maybe_fix_mojibake(raw_text)
                # 步骤2：基础规则清洗（原有逻辑）
                cleaned_text = self._basic_noise_reduction(raw_text)

                # 步骤3：可插拔文本处理器增强（核心改造点）
                if use_text_processor:
                    # HTML 专用增强提示词
                    html_prompt = """请修复以下HTML提取文本的问题，要求：
1. 修正编码乱码、错别字、标点符号错误
2. 去除HTML标签残留、脚本/样式无关内容
3. 优化格式：修复断行、统一缩进、保留段落结构
4. 仅修正错误，不增删原文核心内容"""

                    # 调用插拔式文本处理器
                    enhanced_text = self.text_processor.process(cleaned_text, html_prompt)
                    final_text = enhanced_text
                else:
                    # 禁用处理器时直接使用基础清洗后的文本
                    final_text = cleaned_text

                logger.info(
                    f"[HTMLProcessor] Processed {file_path}, segments: {len(results)}, "
                    f"raw length: {len(raw_text)}, final length: {len(final_text)}"
                )

                return {
                    "success": True,
                    "text": final_text,
                    "error": "",
                    "meta": {
                        "segment_count": len(results),
                        "raw_text_length": len(raw_text),
                        "used_text_processor": use_text_processor,
                        "text_processor_name": self.text_processor.get_processor_name()
                    }
                }

        except Exception as e:
            logger.error(f"[HTMLProcessor] Processing failed {file_path}: {str(e)}")
            return {"success": False, "text": "", "error": f"Exception: {str(e)}"}
