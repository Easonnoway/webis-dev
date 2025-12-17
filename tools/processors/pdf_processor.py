#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Processor
Process PDF files with pluggable text processors
"""
import logging
from typing import Dict, Union, Optional
from .base_processor import BaseFileProcessor
from .text_processors import BaseTextProcessor, DeepSeekTextProcessor, NullTextProcessor

logger = logging.getLogger(__name__)


class PDFProcessor(BaseFileProcessor):
    """PDF Processor - 支持插拔式文本处理器"""

    def __init__(self, text_processor: Optional[BaseTextProcessor] = None):
        """
        初始化PDF处理器
        :param text_processor: 文本处理器实例（不传则默认使用DeepSeek处理器）
        """
        super().__init__()
        self.supported_extensions = {'.pdf'}
        # 注入文本处理器，默认使用DeepSeek
        self.text_processor = text_processor or DeepSeekTextProcessor()

    def get_processor_name(self) -> str:
        return "PDFProcessor"

    def get_supported_extensions(self) -> set:
        return self.supported_extensions

    def extract_text(self, file_path: str) -> Dict[str, Union[str, bool]]:
        """Extract PDF text with pluggable text processing"""
        try:
            from langchain_community.document_loaders import PyPDFLoader

            loader = PyPDFLoader(file_path)
            docs = loader.load()

            text_parts = []
            for i, doc in enumerate(docs, 1):
                page_text = doc.page_content.strip()
                if page_text:
                    text_parts.append(f"--- Page {i} ---\n{page_text}")

            raw_text = "\n\n".join(text_parts)
            logger.info(
                f"[PDFProcessor] 原始文本提取完成：{file_path}, pages: {len(docs)}, text length: {len(raw_text)}")

            # PDF专用处理提示词
            pdf_task_prompt = """请对以下PDF提取文本进行优化，要求：
1. 去除冗余信息：重复页眉页脚、无效符号、连续空白
2. 统一格式：修复断行、对齐页码编号
3. 保留核心内容：分页标记、正文标题列表
4. 不修改原文语义"""

            # 调用插拔式文本处理器
            text = self.text_processor.process(raw_text, pdf_task_prompt)
            if text != raw_text:
                logger.info(
                    f"[PDFProcessor] 使用{self.text_processor.get_processor_name()}处理完成，处理后文本长度：{len(text)}")
            else:
                logger.warning(
                    f"[PDFProcessor] {self.text_processor.get_processor_name()}未执行有效处理")

            logger.info(
                f"[PDFProcessor] Successfully processed PDF: {file_path}, pages: {len(docs)}, text length: {len(text)}")
            return {"success": True, "text": text, "error": ""}

        except ImportError as e:
            error_msg = f"Missing dependency: {str(e)}. Please install: pip install langchain-community pypdf requests tenacity"
            logger.error(f"[PDFProcessor] {error_msg}")
            return {"success": False, "text": "", "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to process PDF: {str(e)}"
            logger.error(f"[PDFProcessor] Failed to process PDF {file_path}: {str(e)}")
            return {"success": False, "text": "", "error": error_msg}
