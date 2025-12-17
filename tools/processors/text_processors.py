#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pluggable Text Processors
Define interface for text processing after extraction
"""
from abc import ABC, abstractmethod
from typing import Optional
import logging
import os
import requests
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


class BaseTextProcessor(ABC):
    """抽象文本处理器 - 定义文本清洗/增强的统一接口"""

    @abstractmethod
    def get_processor_name(self) -> str:
        """返回处理器名称"""
        pass

    @abstractmethod
    def process(self, text: str, task_prompt: str) -> str:
        """处理文本的核心方法"""
        pass


class DeepSeekTextProcessor(BaseTextProcessor):
    """DeepSeek API实现的文本处理器"""

    def __init__(self, api_key: Optional[str] = None, timeout: int = 60, max_retry: int = 3):
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        self.timeout = timeout
        self.max_retry = max_retry

    def get_processor_name(self) -> str:
        return "DeepSeekTextProcessor"

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.Timeout, requests.exceptions.ConnectionError))
    )
    def _send_ai_request(self, api_url: str, payload: dict, headers: dict):
        return requests.post(api_url, json=payload, headers=headers, timeout=self.timeout)

    def process(self, text: str, task_prompt: str) -> str:
        """
        处理文本
        :param text: 原始文本
        :param task_prompt: 任务提示词（不同处理器可定制）
        """
        if not self.api_key:
            logger.warning(f"[{self.get_processor_name()}] 未配置API密钥，跳过处理")
            return text

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 分块处理长文本
            chunk_size = 3000
            text_chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]
            processed_chunks = []

            for chunk in text_chunks:
                prompt = f"{task_prompt}\n\n文本内容：{chunk}"
                api_url = "https://api.siliconflow.cn/v1/chat/completions"
                payload = {
                    "model": "deepseek-ai/DeepSeek-V3",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 2048
                }

                response = self._send_ai_request(api_url, payload, headers)
                response.raise_for_status()
                processed_chunks.append(response.json()["choices"][0]["message"]["content"])

            return "\n\n".join(processed_chunks)

        except Exception as e:
            logger.error(f"[{self.get_processor_name()}] 处理失败：{str(e)}")
            return text


class NullTextProcessor(BaseTextProcessor):
    """空文本处理器 - 不做任何处理"""

    def get_processor_name(self) -> str:
        return "NullTextProcessor"

    def process(self, text: str, task_prompt: str) -> str:
        logger.info(f"[{self.get_processor_name()}] 空处理器，跳过文本处理")
        return text
