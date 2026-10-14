"""
Streamlit dashboard for real-time game agent telemetry.

This module provides a live dashboard that:
- Displays key metrics (session ID, decisions, latest move, fallback count)
- Shows Laya probability distribution as an interactive bar chart
- Displays the compressed context prompt
- Streams the last 15 telemetry log entries
- Auto-refreshes every 1-2 seconds
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List

import streamlit as st
import pandas as pd

from config import LOG_FILE_PATH, SESSION_ID


@st.cache_data(ttl=1)
def load_audit_log() -> List[Dict[str, Any]]:
    """
    Load and parse the audit log JSONL file.
    
    Uses Streamlit's cache with 1-second TTL to enable efficient re-reading.
    
    Returns:
        List of parsed log entries
    """
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            entries = []
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
            return entries
    except FileNotFoundError:
        return []
    except IOError:
        return []


def compute_metrics(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute summary metrics from log entries.
    
    Args:
        entries: List of log entries
        
    Returns:
        Dictionary of computed metrics
    """
    if not entries:
        return {
            "total_decisions": 0,
            "latest_move": "N/A",
            "fallback_count": 0,
            "latest_timestamp": "N/A",
        }
    
    total_decisions = len(entries)
    fallback_count = sum(1 for entry in entries if entry.get("fallback_triggered", False))
    latest_entry = entries[-1]
    latest_move = latest_entry.get("selected_action", "N/A")
    latest_timestamp = latest_entry.get("timestamp", "N/A")
    
    return {
        "total_decisions": total_decisions,
        "latest_move": latest_move,
        "fallback_count": fallback_count,
        "latest_timestamp": latest_timestamp,
    }


def render_metrics(metrics: Dict[str, Any]) -> None:
    """
    Render metric cards at the top of the dashboard.
    
    Args:
        metrics: Dictionary of computed metrics
    """
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Session ID",
            value=SESSION_ID,
        )
    
    with col2:
        st.metric(
            label="Total Decisions",
            value=metrics["total_decisions"],
        )
    
    with col3:
        st.metric(
            label="Latest Move",
            value=metrics["latest_move"],
        )
    
    with col4:
        st.metric(
            label="Fallback Overrides",
            value=metrics["fallback_count"],
            delta=f"{metrics['fallback_count']}" if metrics["total_decisions"] > 0 else None,
        )


def render_probability_chart(latest_entry: Dict[str, Any]) -> None:
    """
    Render an interactive bar chart of Laya's probability distribution.
    
    Args:
        latest_entry: The most recent log entry containing probabilities
    """
    st.subheader("Laya Probability Distribution")
    
    if not latest_entry:
        st.info("No data available yet")
        return
    
    probabilities = latest_entry.get("laya_probabilities", {})
    
    if not probabilities:
        st.info("No probability data available")
        return
    
    # Convert to DataFrame for plotting
    df = pd.DataFrame([
        {"Action": action, "Probability": prob}
        for action, prob in probabilities.items()
    ])
    
    # Sort by probability for better visualization
    df = df.sort_values("Probability", ascending=False)
    
    # Create bar chart
    st.bar_chart(
        data=df,
        x="Action",
        y="Probability",
        use_container_width=True,
    )
    
    # Display top choice with confidence
    top_action = max(probabilities.items(), key=lambda x: x[1])
    st.caption(f"Top Choice: {top_action[0]} (confidence: {top_action[1]:.2%})")


def render_context_box(latest_entry: Dict[str, Any]) -> None:
    """
    Render the compressed context prompt box.
    
    Args:
        latest_entry: The most recent log entry
    """
    st.subheader("Compressed Context Prompt")
    
    if not latest_entry:
        st.info("No context data available yet")
        return
    
    compressed_context = latest_entry.get("compressed_context", "")
    
    if not compressed_context:
        st.info("No context available")
        return
    
    st.text(
        compressed_context,
        height=100,
    )
    
    # Display token count estimate (rough approximation)
    token_estimate = len(compressed_context.split())
    st.caption(f"Estimated tokens: ~{token_estimate}")


def render_log_table(entries: List[Dict[str, Any]]) -> None:
    """
    Render a live data table with the last 15 telemetry entries.
    
    Args:
        entries: List of all log entries
    """
    st.subheader("Recent Telemetry Log")
    
    if not entries:
        st.info("No log entries yet")
        return
    
    # Get last 15 entries
    recent_entries = entries[-15:]
    
    # Create DataFrame for display
    df = pd.DataFrame(recent_entries)
    
    # Select and rename columns for better display
    display_columns = {
        "timestamp": "Timestamp",
        "selected_action": "Action",
        "fallback_triggered": "Fallback",
        "server_status": "Status",
    }
    
    # Filter columns that exist
    available_columns = {k: v for k, v in display_columns.items() if k in df.columns}
    
    if available_columns:
        df_display = df[list(available_columns.keys())].rename(columns=available_columns)
        
        # Format fallback as Yes/No
        if "Fallback" in df_display.columns:
            df_display["Fallback"] = df_display["Fallback"].map({True: "Yes", False: "No"})
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.dataframe(df, use_container_width=True)


def main() -> None:
    """
    Main Streamlit app function.
    """
    st.set_page_config(
        page_title="Game Agent Dashboard",
        page_icon="🤖",
        layout="wide",
    )
    
    st.title("🤖 Track 02: Beat the Bot - Agent Dashboard")
    st.markdown(f"**Session:** {SESSION_ID}")
    
    # Load audit log
    entries = load_audit_log()
    
    # Compute metrics
    metrics = compute_metrics(entries)
    
    # Render metrics
    render_metrics(metrics)
    
    st.divider()
    
    # Create two-column layout
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        # Render probability chart
        latest_entry = entries[-1] if entries else None
        render_probability_chart(latest_entry)
    
    with col_right:
        # Render context box
        render_context_box(latest_entry)
    
    st.divider()
    
    # Render log table
    render_log_table(entries)
    
    # Auto-refresh information
    st.caption("Dashboard auto-refreshes every 1 second")
    
    # Auto-refresh using time.sleep in a loop
    time.sleep(1)
    st.rerun()


if __name__ == "__main__":
    main()
