"""Data-source agent built on LangChain (using create_agent) to route tasks to tools."""


"""

python crawler/agent.py "帮我搜索llm相关文件" --limit 20
"""
from __future__ import annotations

import argparse
import logging
import os
import pathlib
import sys
from typing import Dict, List, Optional

try:
    from dotenv import find_dotenv, load_dotenv
except ImportError:
    find_dotenv = None
    load_dotenv = None

try:
    from langchain.agents import create_agent
    from langchain_core.tools import Tool
except ImportError as exc:  # noqa: BLE001
    raise ImportError(
        "缺少 LangChain 相关依赖，请先安装：`pip install langchain langchain-openai`。"
    ) from exc

if __package__ is None:
    # 允许直接脚本运行：python crawler/agent.py ...
    sys.path.append(str(pathlib.Path(__file__).resolve().parent))
    from ddg_scrapy_tool import DuckDuckGoScrapyTool  # type: ignore  # noqa: E402
    from tool_base import BaseTool, ToolResult  # type: ignore  # noqa: E402
else:
    from .ddg_scrapy_tool import DuckDuckGoScrapyTool  # type: ignore
    from .tool_base import BaseTool, ToolResult  # type: ignore

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def _load_env():
    """Load .env or .env.local if python-dotenv is available."""
    if not find_dotenv or not load_dotenv:
        return
    for fname in (".env.local", ".env"):
        path = find_dotenv(fname, usecwd=True)
        if path:
            load_dotenv(path, override=False)
            logger.info("Loaded environment from %s", path)
            break


class LangChainDataSourceAgent:
    """
    LangChain-based agent: uses an LLM + create_agent to pick and call tools.
    Works with langchain>=1.1（仅暴露 create_agent）.
    """

    def __init__(self, llm, tools: Optional[List[BaseTool]] = None, verbose: bool = False):
        if tools is None:
            tools = []
        self.llm = llm
        self.verbose = verbose
        self.tools: Dict[str, BaseTool] = {tool.name: tool for tool in tools}
        self.lc_tools = [self._wrap_tool_for_langchain(tool) for tool in tools]
        self.agent = self._build_agent()
        self.last_result: Optional[ToolResult] = None

    def register_tool(self, tool: BaseTool):
        self.tools[tool.name] = tool
        self.lc_tools.append(self._wrap_tool_for_langchain(tool))
        self.agent = self._build_agent()
        logger.info("Registered tool: %s", tool.name)

    def available_tools(self) -> List[str]:
        return list(self.tools.keys())

    def run(self, task: str, **kwargs) -> ToolResult:
        logger.info("Agent received task: %s", task)
        self.last_result = None
        # langchain 1.1 create_agent expects messages key
        _ = self.agent.invoke({"messages": [{"role": "user", "content": task}], **kwargs})

        if self.last_result:
            return self.last_result

        return ToolResult(
            name="langchain_agent",
            success=False,
            error="Agent finished without tool result.",
            meta={"raw_output": _},
        )

    def _wrap_tool_for_langchain(self, tool: BaseTool) -> Tool:
        """Wrap BaseTool as a LangChain Tool while capturing the latest result."""

        def _run(task: str, limit: int = 5, **kwargs):
            result = tool.run(task=task, limit=limit, **kwargs)
            self.last_result = result
            if result.success:
                return f"success; output_dir={result.output_dir}; files={len(result.files)}"
            return f"error: {result.error}"

        return Tool(
            name=tool.name,
            description=tool.description,
            func=_run,
        )

    def _build_agent(self):
        return create_agent(
            model=self.llm,
            tools=self.lc_tools,
            system_prompt="你是数据源获取助手。根据用户的任务选择并调用合适的工具。若无合适工具则直接说明。",
        )


def cli():
    parser = argparse.ArgumentParser(description="Data-source agent demo.")
    parser.add_argument("task", help="Natural-language task/keyword to fetch data for.")
    parser.add_argument("--limit", type=int, default=5, help="Max results for crawler tools.")
    parser.add_argument("--model", type=str, default="deepseek-ai/DeepSeek-V3.2", help="LLM model name (SiliconFlow).")
    parser.add_argument("--api-key", type=str, default=None, help="SiliconFlow API key (env SILICONFLOW_API_KEY).")
    args = parser.parse_args()

    _load_env()

    try:
        from langchain_openai import ChatOpenAI
    except ImportError as exc:  # noqa: BLE001
        raise ImportError("需要安装 langchain-openai 才能在 CLI 演示中创建 LLM：`pip install langchain-openai`") from exc

    api_key = args.api_key or os.getenv("SILICONFLOW_API_KEY")
    if not api_key:
        raise RuntimeError("缺少 SiliconFlow API Key，请设置环境变量 SILICONFLOW_API_KEY 或使用 --api-key 传入。")

    llm = ChatOpenAI(
        model=args.model,
        temperature=0,
        base_url="https://api.siliconflow.cn/v1",
        api_key=api_key,
    )
    ddg_tool = DuckDuckGoScrapyTool()
    agent = LangChainDataSourceAgent(llm=llm, tools=[ddg_tool], verbose=True)

    result = agent.run(task=args.task, limit=args.limit)

    if result.success:
        print(f"✓ Agent finished using tool: {result.name}")
        print(f"Output dir: {result.output_dir}")
        print("Files:")
        for f in result.files:
            print(f" - {f}")
    else:
        print(f"✗ Agent failed: {result.error}")


if __name__ == "__main__":
    cli()
