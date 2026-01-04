#!/usr/bin/env python3
"""
Webis Intelligence Radar
------------------------
A multi-source intelligence gathering application that combines:
1. News Search (GNews/SerpApi) - For market buzz and media coverage.
2. Code Search (GitHub) - For developer activity and technical reality.
3. LLM Synthesis - To generate a comprehensive "Market vs. Tech" report.

Usage:
    python3 examples/intelligence_radar.py [TOPIC]
    
    Example: python3 examples/intelligence_radar.py "Agentic AI"
"""

import os
import sys
import logging
import asyncio
import shutil
from typing import List, Dict, Any

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crawler.gnews_tool import GNewsTool
from crawler.serpapi_tool import SerpApiSearchTool
from crawler.github_api_tools import GitHubSearchTool
from tools.processors.html_processor import HTMLProcessor
from structuring.llm import get_default_llm
from langchain_core.messages import HumanMessage, SystemMessage
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Configuration ---
# Load environment variables from .env.local
load_dotenv(".env.local")

def setup_env():
    # Ensure critical keys are present
    required_keys = ["SILICONFLOW_API_KEY"]
    missing = [k for k in required_keys if k not in os.environ]
    if missing:
        logger.warning(f"Missing environment variables: {missing}. Please set them in .env.local")

def simple_extract(filepath: str) -> str:
    """Fallback extraction using BeautifulSoup"""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            text = soup.get_text()
            # Break into lines and remove leading/trailing space on each
            lines = (line.strip() for line in text.splitlines())
            # Break multi-headlines into a line each
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            # Drop blank lines
            text = '\n'.join(chunk for chunk in chunks if chunk)
            return text
    except Exception as e:
        logger.warning(f"Simple extraction failed for {filepath}: {e}")
        return ""

async def process_files(processor, directory: str, source_type: str) -> List[Dict[str, str]]:
    """
    Reads and extracts text from all HTML files in a directory.
    """
    results = []
    if not os.path.exists(directory):
        return results
        
    files = [f for f in os.listdir(directory) if f.endswith(".html")]
    for filename in files:
        filepath = os.path.join(directory, filename)
        try:
            # Try robust processor first
            content = ""
            extraction = processor.process_file(filepath)
            if extraction.get("success") and extraction.get("text"):
                content = extraction["text"]
            else:
                # Fallback
                content = simple_extract(filepath)
            
            if content:
                results.append({
                    "source": source_type,
                    "title": filename.replace(".html", ""),
                    "content": content[:2000]  # Truncate for context window
                })
        except Exception as e:
            logger.warning(f"Failed to process {filename}: {e}")
            
    return results

async def generate_report(llm, topic: str, news_data: List[Dict], code_data: List[Dict]):
    """
    Synthesizes the gathered data into a report.
    """
    logger.info("🧠 Synthesizing Intelligence Report...")
    
    news_context = "\n\n".join([f"Title: {item['title']}\nContent: {item['content']}" for item in news_data])
    code_context = "\n\n".join([f"Repo: {item['title']}\nReadme/Page: {item['content']}" for item in code_data])
    
    prompt = f"""
    You are a Senior Technology Analyst. You have gathered intelligence on the topic: "{topic}".
    
    Here is the latest Media/News coverage:
    {news_context}
    
    Here is the latest Developer/GitHub activity:
    {code_context}
    
    Please write a "Market vs. Tech" Intelligence Report.
    
    Structure:
    1. **Executive Summary**: What is the current state of "{topic}"?
    2. **Media Buzz**: What are people talking about? (Cite specific news items if possible)
    3. **Developer Reality**: What are engineers actually building? (Cite specific repos)
    4. **Gap Analysis**: Is there a disconnect between the hype and the code?
    5. **Conclusion**: Bullish or Bearish?
    
    Keep it professional, insightful, and concise.
    """
    
    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        return f"Error generating report: {e}"

def main():
    setup_env()
    
    # Get topic from args or default
    topic = sys.argv[1] if len(sys.argv) > 1 else "Model Context Protocol"
    
    base_dir = "radar_data"
    news_dir = os.path.join(base_dir, "news")
    code_dir = os.path.join(base_dir, "code")
    
    # Clean up previous run
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    
    logger.info(f"📡 Initializing Intelligence Radar for topic: '{topic}'")
    
    # Initialize Tools
    # We prefer GNews for news, fallback to SerpApi if needed (not implemented here for brevity)
    gnews = GNewsTool(output_dir=news_dir)
    github = GitHubSearchTool(output_dir=code_dir)
    processor = HTMLProcessor()
    
    try:
        llm = get_default_llm()
    except Exception as e:
        logger.error(f"LLM Setup Failed: {e}")
        return

    # Run Collection (Sequential for clarity, could be parallel)
    logger.info("📰 Scanning Global News...")
    gnews_result = gnews.run(task=topic, limit=3)
    
    logger.info("👨‍💻 Scanning GitHub Repositories...")
    github_result = github.run(task=topic, limit=3)
    
    # Process Data
    async def run_pipeline():
        news_items = await process_files(processor, news_dir, "News")
        code_items = await process_files(processor, code_dir, "GitHub")
        
        if not news_items and not code_items:
            logger.error("❌ No data found from any source. Aborting.")
            return

        logger.info(f"✅ Collected {len(news_items)} news articles and {len(code_items)} repositories.")
        
        # Generate Report
        report = await generate_report(llm, topic, news_items, code_items)
        
        print("\n" + "="*60)
        print(f"📊 INTELLIGENCE RADAR REPORT: {topic.upper()}")
        print("="*60)
        print(report)
        print("="*60 + "\n")

    asyncio.run(run_pipeline())

if __name__ == "__main__":
    main()
