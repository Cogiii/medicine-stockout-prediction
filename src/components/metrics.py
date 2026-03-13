"""
Metric card components.
"""
import streamlit as st
from src.utils.icons import get_icon


def render_metric_card(label: str, value, delta=None, icon_name: str = None):
    """
    Render a metric card.

    Args:
        label: Metric label
        value: Metric value
        delta: Optional delta value
        icon_name: Optional icon name
    """
    st.metric(label=label, value=value, delta=delta)


def render_risk_metrics(high_count: int, medium_count: int, low_count: int, total: int):
    """
    Render risk summary metrics in a row.

    Args:
        high_count: Number of HIGH risk items
        medium_count: Number of MEDIUM risk items
        low_count: Number of LOW risk items
        total: Total number of items
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="High Risk",
            value=high_count,
            delta=None,
            help="Likely to run out of stock within 7 days. Order immediately."
        )

    with col2:
        st.metric(
            label="Moderate Risk",
            value=medium_count,
            delta=None,
            help="May run out of stock within 7-14 days. Plan to reorder soon."
        )

    with col3:
        st.metric(
            label="Low Risk",
            value=low_count,
            delta=None,
            help="Enough stock for 14+ days. No immediate action needed."
        )

    with col4:
        st.metric(
            label="Total Items",
            value=total,
            delta=None
        )


def render_stock_metrics(total_stock: int, avg_days: float, risk_score: float):
    """
    Render stock summary metrics.

    Args:
        total_stock: Total stock units
        avg_days: Average days of coverage
        risk_score: Overall risk score
    """
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            label="Total Stock",
            value=f"{total_stock:,}",
            help="Total units in inventory"
        )

    with col2:
        st.metric(
            label="Avg Days Coverage",
            value=f"{avg_days:.0f}",
            help="Average days until stockout"
        )

    with col3:
        st.metric(
            label="Risk Score",
            value=f"{risk_score:.1f}/10",
            help="Overall clinic risk score"
        )
