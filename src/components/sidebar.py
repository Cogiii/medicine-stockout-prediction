"""
Sidebar navigation component.
"""
import streamlit as st
from src.utils.icons import get_icon
import config


def render_sidebar() -> str:
    """
    Render the sidebar navigation.

    Returns:
        Selected page name
    """
    st.sidebar.title(config.APP_NAME)
    st.sidebar.divider()

    # Navigation
    page = st.sidebar.radio(
        "Navigation",
        options=[
            "Risk Dashboard",
            "Stock Overview",
            "Predict"
        ],
        format_func=lambda x: f"{_get_page_icon(x)} {x}",
        label_visibility="collapsed"
    )

    return page


def _get_page_icon(page_name: str) -> str:
    """Get icon for page name."""
    icons = {
        "Risk Dashboard": get_icon("dashboard"),
        "Stock Overview": get_icon("inventory"),
        "Predict": get_icon("predict")
    }
    return icons.get(page_name, "")
