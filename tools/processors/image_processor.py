#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Image OCR Processor with pluggable text processors
"""

import logging
from typing import Dict, Union, Optional
from .base_processor import BaseFileProcessor
from .text_processors import BaseTextProcessor, DeepSeekTextProcessor, NullTextProcessor

logger = logging.getLogger(__name__)


class ImageProcessor(BaseFileProcessor):
    """Image OCR Processor - Uses EasyOCR with pluggable text processing"""

    def __init__(self, text_processor: Optional[BaseTextProcessor] = None):
        super().__init__()
        self.supported_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif'}
        self._reader = None
        # 注入文本处理器，默认使用DeepSeek
        self.text_processor = text_processor or DeepSeekTextProcessor()

    def get_processor_name(self) -> str:
        return "ImageProcessor"

    def get_supported_extensions(self) -> set:
        return self.supported_extensions

    def _get_reader(self):
        """Lazy load EasyOCR to avoid loading model at startup"""
        if self._reader is None:
            try:
                import easyocr
                logger.info("[ImageProcessor] Initializing EasyOCR model...")
                self._reader = easyocr.Reader(['ch_sim', 'en'])
                logger.info("[ImageProcessor] EasyOCR model initialization completed")
            except ImportError:
                raise ImportError("Please install easyocr: pip install easyocr")
        return self._reader

    def extract_text(self, file_path: str) -> Dict[str, Union[str, bool]]:
        """
        Extract text from image with pluggable text processing
        """
        try:
            reader = self._get_reader()
            results = reader.readtext(file_path)

            # 提取OCR识别文本
            text_lines = []
            for (bbox, text, confidence) in results:
                if confidence > 0.5:  # 过滤低置信度结果
                    text_lines.append(text.strip())

            raw_text = "\n".join(text_lines)
            logger.info(f"[ImageProcessor] OCR完成：{file_path}, 识别行数: {len(text_lines)}")

            # OCR文本专用处理提示词
            ocr_task_prompt = """请对以下OCR识别文本进行优化，要求：
1. 修正识别错误：错别字、乱码
2. 修复格式：断句、段落划分
3. 保留所有识别内容，不添加额外信息"""

            # 调用插拔式文本处理器
            text = self.text_processor.process(raw_text, ocr_task_prompt)

            logger.info(f"[ImageProcessor] 处理完成：{file_path}, 文本长度: {len(text)}")
            return {"success": True, "text": text, "error": ""}

        except ImportError as e:
            error_msg = f"Missing dependency: {str(e)}. Please install: pip install easyocr"
            logger.error(f"[ImageProcessor] {error_msg}")
            return {"success": False, "text": "", "error": error_msg}
        except Exception as e:
            error_msg = f"Failed to process image: {str(e)}"
            logger.error(f"[ImageProcessor] Failed to process image {file_path}: {str(e)}")
            return {"success": False, "text": "", "error": error_msg}
