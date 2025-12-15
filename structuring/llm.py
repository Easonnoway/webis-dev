"""LLM factory for structuring agents (SiliconFlow + DeepSeek)."""

from __future__ import annotations

import os
from typing import Optional

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:  # pragma: no cover
    find_dotenv = None
    load_dotenv = None

from langchain_openai import ChatOpenAI


def load_env():
    """Load .env.local or .env from CWD if python-dotenv is installed."""
    if not find_dotenv or not load_dotenv:
        return
    for fname in (".env.local", ".env"):
        path = find_dotenv(fname, usecwd=True)
        if path:
            load_dotenv(path, override=False)
            break


def get_default_llm(
    api_key: Optional[str] = None,
    model: str = "deepseek-ai/DeepSeek-V3.2",
    base_url: str = "https://api.siliconflow.cn/v1",
    temperature: float = 0.0,
):
    """Create default SiliconFlow LLM client."""
    load_env()
    key = api_key or os.getenv("SILICONFLOW_API_KEY")
    if not key:
        raise RuntimeError(
            "缺少 SILICONFLOW_API_KEY，请设置环境变量或在 get_default_llm(api_key=...) 传入。"
        )
    return ChatOpenAI(model=model, base_url=base_url, api_key=key, temperature=temperature)
