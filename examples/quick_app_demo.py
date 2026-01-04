#!/usr/bin/env python3
"""
Webis Quick App Demo: Tech Trend Tracker
----------------------------------------
This script demonstrates how to quickly build an interesting application using Webis.
It fetches the top stories from Hacker News, extracts their content, and uses an LLM
to generate a "TL;DR" summary and a "Why it matters" analysis.

Prerequisites:
- pip install requests langchain-openai
- Set SILICONFLOW_API_KEY environment variable (for the LLM)
"""

import os
import sys
import logging
import asyncio
from typing import List, Dict

# Add project root to path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from crawler.hn_tool import HackerNewsTool
from tools.processors.html_processor import HTMLProcessor
from structuring.llm import get_default_llm
from langchain_core.messages import HumanMessage, SystemMessage

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def analyze_story(llm, title: str, content: str) -> Dict[str, str]:
    """
    Uses the LLM to analyze a single story.
    """
    if not content or len(content) < 100:
        return {"summary": "Content too short or failed to extract.", "impact": "N/A"}

    # Truncate content to avoid token limits (simple approach)
    truncated_content = content[:4000]

    prompt = f"""
    You are a tech trend analyst. Analyze the following article content.
    
    Title: {title}
    Content: {truncated_content}
    
    Please provide:
    1. A one-sentence TL;DR summary.
    2. A short explanation of why this matters to the tech industry.
    
    Format your response as:
    TL;DR: [Summary]
    Impact: [Impact]
    """

    try:
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        text = response.content
        
        # Simple parsing (robustness could be improved)
        summary = "N/A"
        impact = "N/A"
        
        for line in text.split('\n'):
            if line.startswith("TL;DR:"):
                summary = line.replace("TL;DR:", "").strip()
            elif line.startswith("Impact:"):
                impact = line.replace("Impact:", "").strip()
                
        # Fallback if parsing fails but we got text
        if summary == "N/A" and text:
            summary = text[:100] + "..."

        return {"summary": summary, "impact": impact}
    except Exception as e:
        logger.error(f"LLM analysis failed: {e}")
        return {"summary": "Error during analysis", "impact": str(e)}

def main():
    # 1. Setup
    output_dir = "temp_hn_data"
    os.makedirs(output_dir, exist_ok=True)
    
    logger.info("🚀 Starting Webis Tech Trend Tracker...")

    # 2. Initialize Tools
    hn_tool = HackerNewsTool(output_dir=output_dir)
    html_processor = HTMLProcessor()
    
    try:
        llm = get_default_llm()
    except RuntimeError as e:
        logger.error(f"Setup Error: {e}")
        logger.info("Please set SILICONFLOW_API_KEY to run the analysis.")
        return

    # 3. Fetch Data (Top 3 stories for speed)
    logger.info("📰 Fetching top stories from Hacker News...")
    result = hn_tool.run(task="fetch top stories", limit=3)
    
    if not result.success:
        logger.error("Failed to fetch stories.")
        return

    # 4. Process and Analyze
    logger.info("🧠 Analyzing stories with LLM...")
    
    # We'll use asyncio to run LLM calls if we were doing many, 
    # but for simplicity in this sync main(), we'll just run the loop.
    # Since get_default_llm returns a ChatOpenAI which has async methods, 
    # let's wrap the analysis in an async runner.
    
    async def run_analysis():
        files = [f for f in os.listdir(output_dir) if f.endswith(".html")]
        
        for filename in files:
            filepath = os.path.join(output_dir, filename)
            
            # Extract text
            logger.info(f"Processing {filename}...")
            extraction_result = html_processor.process(filepath)
            
            if not extraction_result.success:
                logger.warning(f"Failed to extract content from {filename}")
                continue
                
            content = extraction_result.content
            # HN Tool doesn't save title in filename, so we'll just use filename as proxy or extract from content
            title = filename # In a real app, we'd pass metadata better
            
            # Analyze
            analysis = await analyze_story(llm, title, content)
            
            # Output
            print("\n" + "="*50)
            print(f"📄 File: {filename}")
            print(f"📝 TL;DR: {analysis['summary']}")
            print(f"💡 Impact: {analysis['impact']}")
            print("="*50 + "\n")

    asyncio.run(run_analysis())
    
    logger.info("✅ Done! Check the output above.")

if __name__ == "__main__":
    main()
