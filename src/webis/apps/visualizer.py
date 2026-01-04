import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
# from webis.core.memory.db import get_db_session # Assuming we have this
# from webis.core.memory.models import PipelineRun, Document # Assuming we have this

st.set_page_config(page_title="Webis Visualizer Pro", layout="wide")

st.title("Webis Platform Dashboard")

# Sidebar
st.sidebar.header("Navigation")
page = st.sidebar.radio("Go to", ["Overview", "Pipeline Runs", "Knowledge Base", "Search"])

# Mock data for now since DB connection might not be fully ready/configured in this env
def get_mock_stats():
    return {
        "total_documents": 1250,
        "total_runs": 45,
        "total_tokens": 1500000,
        "avg_cost_per_run": 0.05
    }

def get_mock_runs():
    data = []
    for i in range(10):
        data.append({
            "run_id": f"run-{i}",
            "task": f"Analyze company {i}",
            "status": "completed" if i % 3 != 0 else "failed",
            "started_at": datetime.now().isoformat(),
            "duration": 12.5 + i,
            "tokens": 1000 * i
        })
    return pd.DataFrame(data)

if page == "Overview":
    st.header("System Overview")
    stats = get_mock_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Documents", stats["total_documents"])
    col2.metric("Total Runs", stats["total_runs"])
    col3.metric("Total Tokens", f"{stats['total_tokens']:,}")
    col4.metric("Avg Cost ($)", stats["avg_cost_per_run"])
    
    st.subheader("Recent Activity")
    st.line_chart([10, 20, 15, 25, 30, 20, 40]) # Mock chart

elif page == "Pipeline Runs":
    st.header("Pipeline Runs")
    df = get_mock_runs()
    st.dataframe(df)

elif page == "Knowledge Base":
    st.header("Knowledge Base Explorer")
    st.info("Connect to Vector Store/DB to browse documents.")

elif page == "Search":
    st.header("Semantic Search")
    query = st.text_input("Enter query")
    if query:
        st.write(f"Searching for: {query}...")
        # Here we would call HybridRetriever
        st.success("Found 3 results (Mock)")
        st.json([
            {"content": "Result 1 content...", "score": 0.9},
            {"content": "Result 2 content...", "score": 0.85},
        ])

if __name__ == "__main__":
    # This allows running with `streamlit run src/webis/apps/visualizer.py`
    pass
