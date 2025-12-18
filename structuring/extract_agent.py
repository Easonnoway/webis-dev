"""StructureExtractionAgent: execute structured extraction based on built prompt."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union

from langchain_core.messages import HumanMessage, SystemMessage


OutputFormat = Literal["json", "markdown", "table"]


@dataclass
class ExtractionResult:
    success: bool
    output_format: OutputFormat
    raw: str
    parsed: Optional[Union[Dict[str, Any], List[Any], str]] = None
    error: Optional[str] = None


class StructureExtractionAgent:
    """
    调用大模型执行结构化抽取。
    - prompt 由 PromptBuilderAgent 生成
    - output_format 控制最终输出类型
    """

    def __init__(self, llm):
        self.llm = llm

    def extract(
        self,
        prompt: str,
        text: Union[str, List[str]],
        output_format: OutputFormat = "json",
    ) -> ExtractionResult:
        combined_text = "\n\n".join(text) if isinstance(text, list) else text

        raw = self._invoke_llm(prompt, combined_text)

        if output_format == "json":
            try:
                parsed = self._safe_json_parse(raw)
                return ExtractionResult(True, output_format, raw=raw, parsed=parsed)
            except Exception as exc:  # noqa: BLE001
                return ExtractionResult(False, output_format, raw=raw, error=str(exc))

        return ExtractionResult(True, output_format, raw=raw, parsed=raw)

    def _invoke_llm(self, prompt: str, text: str) -> str:
        """
        直接用 messages 调用 LLM，避免 ChatPromptTemplate 把 JSON 示例里的 `{}` 当成变量导致 KeyError。
        """
        system = (
            "你是结构抽取助手。严格按上游提供的抽取 Prompt 执行。"
            "不要编造信息；若文本缺失字段请返回空/未知。\n\n"
            f"抽取 Prompt：\n{prompt}\n"
        )
        user = f"输入文本：\n{text}\n\n请按抽取 Prompt 输出结果。"
        resp = self.llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return getattr(resp, "content", "") or ""

    def _safe_json_parse(self, raw: str):
        # remove fenced blocks if any
        fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", raw, re.S)
        candidate = fenced.group(1) if fenced else raw
        candidate = candidate.strip()
        return json.loads(candidate)
