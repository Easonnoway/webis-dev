#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Document Processor
Process doc/docx/txt/md files with pluggable text processors
"""

import logging
from typing import Dict, Union, Optional
from .base_processor import BaseFileProcessor
from .text_processors import BaseTextProcessor, DeepSeekTextProcessor, NullTextProcessor

logger = logging.getLogger(__name__)


class DocumentProcessor(BaseFileProcessor):
    """Document Processor - Process doc/docx/txt/md files"""

    def __init__(self, text_processor: Optional[BaseTextProcessor] = None):
        super().__init__()
        self.supported_extensions = {'.doc', '.docx', '.txt', '.md'}
        # 注入文本处理器，默认使用DeepSeek
        self.text_processor = text_processor or DeepSeekTextProcessor()

    def get_processor_name(self) -> str:
        return "DocumentProcessor"

    def get_supported_extensions(self) -> set:
        return self.supported_extensions

    def extract_text(self, file_path: str) -> Dict[str, Union[str, bool]]:
        """
        Extract document text with pluggable text processing
        """
        try:
            from langchain_community.document_loaders import Docx2txtLoader, TextLoader
            import pathlib

            ext = pathlib.Path(file_path).suffix.lower()

            if ext in [".docx", ".doc"]:
                # 使用docx2txt加载器处理Word文档
                loader = Docx2txtLoader(file_path)
                docs = loader.load()
            elif ext in [".txt", ".md"]:
                loader = TextLoader(file_path, encoding="utf-8")
                docs = loader.load()
            else:
                return {"success": False, "text": "", "error": f"Unsupported file type: {ext}"}

            # 合并所有文档内容
            raw_text = "\n".join(doc.page_content for doc in docs).strip()
            logger.info(
                f"[DocumentProcessor] 原始文本提取完成：{file_path}, 文本长度：{len(raw_text)}")

            # 文档专用处理提示词
            doc_task_prompt = """请对以下文档文本进行优化，要求：
1. 表格专项处理：修复错乱，用|分隔单元格
2. 去除冗余：重复页眉页脚、无效符号
3. 统一格式：全角转半角、修复断行
4. 保留所有有意义内容和逻辑结构"""

            # 调用插拔式文本处理器
            text = self.text_processor.process(raw_text, doc_task_prompt)
            if text != raw_text:
                logger.info(
                    f"[DocumentProcessor] 使用{self.text_processor.get_processor_name()}处理完成，处理后文本长度：{len(text)}")
            else:
                logger.warning(f"[DocumentProcessor] {self.text_processor.get_processor_name()}未执行有效处理")

            logger.info(
                f"[DocumentProcessor] Successfully processed document: {file_path}, text length: {len(text)}")
            return {"success": True, "text": text, "error": ""}

        except ImportError as e:
            error_msg = f"Missing dependency: {str(e)}. Please install: pip install langchain-community docx2txt requests tenacity"
            logger.error(f"[DocumentProcessor] {error_msg}")
            return {"success": False, "text": "", "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to process document: {str(e)}"
            logger.error(f"[DocumentProcessor] Failed to process document {file_path}: {str(e)}")
            return {"success": False, "text": "", "error": error_msg}
