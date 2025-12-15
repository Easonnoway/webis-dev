"""StructureExtractionAgent: execute structured extraction based on built prompt."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Literal, Optional, Union

from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


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

        chain = self._build_chain(prompt, output_format)
        raw = chain.invoke({"text": combined_text})

        if output_format == "json":
            try:
                parsed = self._safe_json_parse(raw)
                return ExtractionResult(True, output_format, raw=raw, parsed=parsed)
            except Exception as exc:  # noqa: BLE001
                return ExtractionResult(False, output_format, raw=raw, error=str(exc))

        return ExtractionResult(True, output_format, raw=raw, parsed=raw)

    def _build_chain(self, prompt: str, output_format: OutputFormat):
        # ChatPromptTemplate uses `{var}` for templating. The upstream prompt often contains
        # JSON examples like `{ "items": [...] }`, which would be treated as template vars.
        # Escape braces so the prompt is treated as literal text.
        escaped_prompt = prompt.replace("{", "{{").replace("}", "}}")
        system = (
            "你是结构抽取助手。严格按上游提供的抽取 Prompt 执行。"
            "不要编造信息；若文本缺失字段请返回空/未知。\n\n"
            f"抽取 Prompt：\n{escaped_prompt}\n"
        )
        tpl = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", "输入文本：\n{text}\n\n请按抽取 Prompt 输出结果。"),
            ]
        )

        if output_format == "json":
            return tpl | self.llm | StrOutputParser()
        return tpl | self.llm | StrOutputParser()

    def _safe_json_parse(self, raw: str):
        # remove fenced blocks if any
        fenced = re.search(r"```(?:json)?\s*(\{.*?\}|\[.*?\])\s*```", raw, re.S)
        candidate = fenced.group(1) if fenced else raw
        candidate = candidate.strip()
        return json.loads(candidate)
