"""
Styled dataframe components.
"""
import pandas as pd
import streamlit as st
from src.utils.icons import get_icon


def render_risk_table(df: pd.DataFrame, height: int = 400):
    """
    Render risk alerts table with styling.

    Args:
        df: DataFrame with risk data
        height: Table height in pixels
    """
    # Prepare display columns
    display_df = df[[
        'clinic_name', 'medicine_name', 'medicine_category',
        'stockout_probability', 'risk_level', 'days_until_stockout',
        'ending_stock', 'reorder_urgency', 'reorder_action'
    ]].copy()

    display_df.columns = [
        'Clinic', 'Medicine', 'Category', 'Risk %', 'Risk Level',
        'Days Left', 'Stock', 'Urgency', 'Action'
    ]

    # Format percentage
    display_df['Risk %'] = (display_df['Risk %'] * 100).round(0).astype(int).astype(str) + '%'

    # Sort by risk level
    risk_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}
    display_df['_sort'] = display_df['Risk Level'].map(risk_order)
    display_df = display_df.sort_values('_sort').drop('_sort', axis=1)

    # Convert risk levels to user-friendly labels
    display_df['Risk Level'] = display_df['Risk Level'].apply(_get_risk_label)

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config={
            "Risk Level": st.column_config.TextColumn(
                "Risk Level",
                help="High = may run out in 7 days, Moderate = 7-14 days, Low = 14+ days"
            ),
            "Days Left": st.column_config.NumberColumn(
                "Days Left",
                help="Estimated days until stockout",
                format="%d"
            ),
            "Stock": st.column_config.NumberColumn(
                "Stock",
                help="Current stock units",
                format="%d"
            )
        }
    )


def render_stock_table(df: pd.DataFrame, height: int = 400):
    """
    Render stock overview table.

    Args:
        df: DataFrame with stock data
        height: Table height in pixels
    """
    display_df = df[[
        'medicine_name', 'category', 'current_stock',
        'avg_consumption', 'stockout_rate'
    ]].copy()

    display_df.columns = ['Medicine', 'Category', 'Stock', 'Daily Usage', 'Stockout %']

    # Calculate days coverage
    display_df['Days Coverage'] = (
        display_df['Stock'] / display_df['Daily Usage'].replace(0, 0.1)
    ).round(0).astype(int)

    display_df['Stockout %'] = display_df['Stockout %'].astype(str) + '%'

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        height=height,
        column_config={
            "Stock": st.column_config.NumberColumn(
                "Stock",
                format="%d"
            ),
            "Daily Usage": st.column_config.NumberColumn(
                "Daily Usage",
                format="%.1f"
            ),
            "Days Coverage": st.column_config.NumberColumn(
                "Days Coverage",
                format="%d"
            )
        }
    )


def _get_location_label(score: float) -> str:
    """Convert remoteness score to user-friendly label."""
    if score <= 0.3:
        return "Easy to Reach"
    elif score <= 0.5:
        return "Moderate Access"
    elif score <= 0.7:
        return "Hard to Reach"
    else:
        return "Very Hard to Reach"


def _get_risk_label(level: str) -> str:
    """Convert risk level to user-friendly label."""
    labels = {
        'HIGH': 'High Risk',
        'MEDIUM': 'Moderate Risk',
        'LOW': 'Low Risk'
    }
    return labels.get(level, level)


def render_clinic_table(df: pd.DataFrame):
    """
    Render clinic summary table.

    Args:
        df: DataFrame with clinic summary data
    """
    display_df = df[[
        'clinic_name', 'remoteness_score', 'population_served',
        'stockout_rate', 'total_stock', 'medicine_count'
    ]].copy()

    # Convert remoteness to user-friendly label
    display_df['remoteness_score'] = display_df['remoteness_score'].apply(_get_location_label)

    display_df.columns = [
        'Clinic', 'Location', 'Population',
        'Stockout %', 'Total Stock', 'Medicines'
    ]

    display_df['Stockout %'] = display_df['Stockout %'].astype(str) + '%'

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Population": st.column_config.NumberColumn(
                "Population",
                format="%d"
            ),
            "Total Stock": st.column_config.NumberColumn(
                "Total Stock",
                format="%d"
            )
        }
    )
