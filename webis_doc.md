# Webis 平台系统文档

本文档系统梳理了 Webis 平台目前具备的数据源能力、核心处理流程以及支持的应用场景。

## 1. 数据源 (Data Sources)

Webis 集成了多种数据获取工具，覆盖新闻、代码、学术和通用搜索等领域。所有工具均位于 `crawler/` 目录下。

| 数据源组件 | 对应文件 | 描述 | 依赖配置 (环境变量) |
| :--- | :--- | :--- | :--- |
| **Hacker News** | `crawler/hn_tool.py` | 获取 Hacker News 热门科技新闻及评论，自动抓取原网页内容。 | 无 |
| **GNews** | `crawler/gnews_tool.py` | 全球新闻搜索，支持多语言、多地区筛选。 | `GNEWS_API_KEY` |
| **SerpApi (Google)** | `crawler/serpapi_tool.py` | 基于 Google 搜索的通用信息获取，支持高精度搜索。 | `SERPAPI_API_KEY` |
| **GitHub** | `crawler/github_api_tools.py` | 搜索开源代码仓库，获取 README 和项目元数据。 | `GITHUB_TOKEN` (可选，防限流) |
| **Baidu Search** | `crawler/baidu_mcp_tool.py` | 百度搜索集成，适合中文环境信息获取。 | `BAIDU_AISEARCH_BEARER` |
| **Semantic Scholar** | `crawler/semantic_scholar.py` | 学术论文搜索，获取论文摘要、引用等信息。 | 无 |
| **DuckDuckGo** | `crawler/ddg_scrapy_tool.py` | 隐私优先的通用搜索，无需 API Key。 | 无 |

## 2. 中间处理流程 (Intermediate Processes)

数据获取后，Webis 提供了一套完整的处理管道，将非结构化数据转化为结构化知识。

### 2.1 文件处理与清洗 (Processors)
位于 `tools/processors/`，负责将不同格式的原始文件转换为纯文本。

*   **HTMLProcessor** (`html_processor.py`):
    *   基于 `webis-html` 库提取网页正文。
    *   **智能增强**: 支持调用 DeepSeek 模型修复乱码、纠正排版错误。
    *   **Fallback**: 内置 BeautifulSoup 基础提取模式，确保高可用性。
*   **PDFProcessor** (`pdf_processor.py`): 解析 PDF 文档，提取文本内容。
*   **ImageProcessor** (`image_processor.py`): 集成 OCR 功能，从图片中提取文字。
*   **DocumentProcessor** (`document_processor.py`): 处理 Word (.docx) 和纯文本文件。

### 2.2 核心管道 (Core Pipeline)
位于 `src/webis/core/`，负责任务调度和执行。

*   **Pipeline Engine** (`pipeline.py`): 支持定义 Source -> Processor -> Extractor 的多阶段工作流。
*   **BatchProcessor** (`llm/batcher.py`): 
    *   **功能**: 自动聚合多个小请求为批次处理，优化 LLM 调用成本和吞吐量。
    *   **特性**: 智能超时控制 (Smart Timeout)，防止忙等待。
*   **StreamPipeline** (`pipeline/stream.py`): 支持流式处理，适合实时性要求高的任务。
*   **DistributedExecutor** (`execution/distributed_executor.py`): 支持多线程/多进程并行执行任务。

### 2.3 结构化与智能分析 (Structuring & Intelligence)
位于 `structuring/`。

*   **LLM Factory** (`llm.py`): 统一管理 LLM 连接，默认支持 **SiliconFlow (DeepSeek-V3/R1)**。
*   **Extract Agent**: 基于 Schema 的信息提取智能体。

## 3. 应用场景与可视化 (Applications & Visualization)

基于上述能力，Webis 支持构建多种高级应用。

### 3.1 现有应用示例

1.  **Tech Trend Tracker (科技趋势追踪器)**
    *   **位置**: `examples/quick_app_demo.py`
    *   **流程**: Hacker News 抓取 -> HTML 清洗 -> LLM 摘要 (TL;DR & Impact)。
    *   **价值**: 快速获取每日科技动态。

2.  **Intelligence Radar (情报雷达)**
    *   **位置**: `examples/intelligence_radar.py`
    *   **流程**: GNews (媒体风向) + GitHub (技术落地) -> 多源融合 -> "Market vs. Tech" 深度报告。
    *   **价值**: 辅助投资决策、技术选型调研。

### 3.2 可视化生成 (Visualization)
位于 `visualization/visual.py`。

*   **智能网页生成**: 使用 DeepSeek-R1 模型，将任意文本报告转化为设计精美的 HTML5 网页。
*   **多格式导出**:
    *   **PDF**: 自动排版，支持中文渲染。
    *   **PPT**: 自动生成演示文稿，包含标题和要点。

## 4. 快速开始配置清单

要完整运行 Webis 的所有功能，建议配置以下环境变量 (`.env.local`)：

```bash
# 核心大模型能力 (必须)
SILICONFLOW_API_KEY="sk-..."

# 数据源增强 (按需)
GNEWS_API_KEY="..."
SERPAPI_API_KEY="..."
GITHUB_TOKEN="..."
BAIDU_AISEARCH_BEARER="..."
```
