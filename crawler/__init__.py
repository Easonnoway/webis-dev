"""
Crawler package: provides data-source tools and routing agent.

Current tools:
- DuckDuckGo + Scrapy crawler (see ddg_scrapy_tool.py)

The agent in agent.py can route natural language tasks to tools.
"""

__all__ = ["agent", "ddg_scrapy_tool", "tool_base"]
