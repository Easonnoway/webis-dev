"""Standalone demo for structuring module."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from extract_agent import StructureExtractionAgent
from llm import get_default_llm
from prompt_agent import PromptBuilderAgent
from validation.manager import EnhancedValidationManager  # 新增


def read_texts(inputs):
    paths = []
    for p in inputs:
        path = Path(p)
        if path.is_dir():
            # 默认读取该目录下的所有 .txt 文件（不递归）
            paths.extend(sorted(path.glob("*.txt")))
        else:
            paths.append(path)

    if not paths:
        raise FileNotFoundError("inputs 为空：未找到可读取的文本文件（*.txt）。")

    texts = []
    for path in paths:
        texts.append(path.read_text(encoding="utf-8"))
    return texts


def main():
    parser = argparse.ArgumentParser(description="Structuring module demo.")
    parser.add_argument("goal", help="用户的结构化目标（自然语言）")
    parser.add_argument(
        "--inputs",
        nargs="+",
        required=True,
        help="输入纯文本文件路径列表，或目录路径（目录默认读取其中所有 *.txt，不递归）",
    )
    # 按你的需求，CLI 只保留 goal + inputs 两个参数；其它行为使用默认值：
    # - 自动推断 output_format（json/markdown/table）
    # - 自动保存结果到 structuring/outputs/

    args = parser.parse_args()

    llm = get_default_llm()
    texts = read_texts(args.inputs)

    prompt_agent = PromptBuilderAgent(llm)
    extraction_agent = StructureExtractionAgent(llm)

    prompt, output_format = prompt_agent.build_with_format(
        goal=args.goal,
        texts=texts,
        schema=None,
        few_shots=[],
    )
    print("\n===== Generated Extraction Prompt =====\n")
    print(prompt)

    result = extraction_agent.extract(prompt=prompt, text=texts, output_format=output_format)
    print("\n===== Extraction Result =====\n")

    # Prepare result text for saving and validation loop
    if result.output_format == "json" and result.parsed is not None:
        print(json.dumps(result.parsed, ensure_ascii=False, indent=2))
        result_text = json.dumps(result.parsed, ensure_ascii=False)
    else:
        print(result.raw)
        result_text = result.raw

    # Optional validation/optimization loop (keep CLI minimal: controlled by env var)
    # Enable by: export STRUCTURING_VALIDATE=1
    optimization_result = None
    if os.getenv("STRUCTURING_VALIDATE") == "1" and result.success:
        config_path = Path(__file__).resolve().parent / "config.json"
        validator_config = {}
        if config_path.exists():
            try:
                validator_config = json.loads(config_path.read_text(encoding="utf-8"))
            except Exception:
                validator_config = {}

        enhanced_validator = EnhancedValidationManager(llm, validator_config)
        optimization_result = enhanced_validator.run_validation_loop(
            initial_prompt=prompt,
            initial_result=result_text,
            original_text=texts,
            original_goal=args.goal,
            max_retries=2,
            prompt_agent=prompt_agent,
            extraction_agent=extraction_agent,
            output_format=output_format,
        )

        prompt = optimization_result.get("final_prompt", prompt)
        result_text = optimization_result.get("final_result", result_text)

        if "final_score" in optimization_result:
            print(f"\n最终质量得分: {optimization_result['final_score']:.2f}/5")
        if "optimization_count" in optimization_result:
            print(f"优化轮次: {optimization_result['optimization_count']}")

    # Save outputs to file
    outputs_dir = Path(__file__).resolve().parent / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = "json" if output_format == "json" else "md"
    out_path = outputs_dir / f"structuring_result_{ts}.{suffix}"

    out_path.write_text(result_text, encoding="utf-8")

    print(f"\n已保存结果到: {out_path}")

    prompt_path = out_path.with_suffix(out_path.suffix + ".prompt.txt")
    prompt_path.write_text(prompt, encoding="utf-8")
    print(f"已保存 Prompt 到: {prompt_path}")

    if os.getenv("STRUCTURING_VALIDATE") == "1" and optimization_result is not None:
        history_path = out_path.with_suffix(out_path.suffix + ".validation_history.json")
        try:
            serializable_history = convert_to_serializable(optimization_result.get("history", []))
            history_path.write_text(json.dumps(serializable_history, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"已保存优化历史到: {history_path}")
        except Exception:
            pass


def convert_to_serializable(obj):
    """递归地将对象转换为可JSON序列化的格式"""
    if hasattr(obj, '__dict__'):
        # 如果是对象，转换为字典
        result = {}
        for key, value in obj.__dict__.items():
            if not key.startswith('_'):  # 排除私有属性
                result[key] = convert_to_serializable(value)
        return result
    elif isinstance(obj, (list, tuple)):
        # 如果是列表或元组，递归处理每个元素
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        # 如果是字典，递归处理每个值
        return {key: convert_to_serializable(value) for key, value in obj.items()}
    else:
        # 基本数据类型直接返回
        return obj

if __name__ == "__main__":
    main()
