# Webis Platform

<div align="center">

![Webis Logo](https://via.placeholder.com/150x150.png?text=Webis)

**From Web to Wisdom: Your AI-Powered Knowledge Pipeline**

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

[English](README.md) | [中文](README_CN.md)

</div>

---

**Webis** is a comprehensive, modular, and extensible **LLM Infrastructure Platform** designed to transform unstructured web data into high-quality, structured knowledge assets.

Unlike simple scraper scripts, Webis is built as a **platform** with a "Knowledge Lakehouse" architecture, enabling you to build intelligent applications like Industry Research Generators, RAG Chatbots, and Real-time Monitors on top of your data.

## 🌟 Key Features

- **🔌 Everything is a Plugin**: Modular architecture for Data Sources (Crawlers) and Processors (Cleaners/Extractors).
- **🧠 Intelligent Kernel**: Built-in LLM abstraction layer supporting OpenAI, DeepSeek, Claude, and local models.
- **💾 Knowledge Lakehouse**: Persist raw data, structured JSON, and vector embeddings with full lineage tracking.
- **🛡️ Enterprise Ready**: Type-safe schemas (Pydantic), comprehensive logging, and cost tracking.
- **🚀 Application Ecosystem**: Ready-to-use recipes for Research Reports, News Monitoring, and more.

## 🏗️ Architecture

Webis is organized into three layers:

1.  **Ingestion Layer (Plugins)**:
    *   **Sources**: Google News, GitHub, arXiv, Firecrawl, Local Files...
    *   **Processors**: HTML Cleaning, PDF OCR, PII Redaction, Text Chunking...
2.  **Kernel Layer (Core)**:
    *   **Pipeline Engine**: DAG-based execution with retries and error handling.
    *   **LLM Router**: Smart model selection and fallback strategies.
    *   **Storage**: Metadata (SQL) + Vectors (Chroma/Milvus).
3.  **Application Layer (Service)**:
    *   REST API (FastAPI)
    *   Python SDK
    *   Visualizers & Dashboards

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- API Key for LLM (e.g., OpenAI, DeepSeek, SiliconFlow)

### Installation

```bash
# Clone the repository
git clone https://github.com/Easonnoway/webis-dev.git
cd webis-dev

# Install in editable mode
pip install -e ".[dev]"
```

### Basic Usage

```python
from webis import Pipeline

# Initialize a pipeline with a preset configuration
pipe = Pipeline.from_preset("news_analyst")

# Run the pipeline
result = pipe.run("Analyze the latest trends in Generative AI")

# Access structured results
for item in result.structured_results:
    print(item.data)
```

## 🗺️ Roadmap

We are currently in **Phase 1 (Foundation)** of our v2.0 roadmap.

- [x] **Foundation**: Core schemas, Plugin system, CI/CD.
- [ ] **Memory**: Database integration, Vector store, Deduplication.
- [ ] **Service**: FastAPI server, Python SDK, Task queue.
- [ ] **Intelligence**: Graph RAG, Agentic workflows, Self-correction.

See [TODO.md](TODO.md) for the detailed roadmap.

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the Apache-2.0 License.
