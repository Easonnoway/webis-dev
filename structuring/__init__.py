"""
Structuring module: turn clean texts into structured outputs.

Agents:
- PromptBuilderAgent: build extraction prompts from user goals + texts.
- StructureExtractionAgent: call LLM with prompt to produce JSON/MD/Table.
"""

__all__ = ["llm", "prompt_agent", "extract_agent"]
