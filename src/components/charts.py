"""
Chart components.
"""
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st


def render_bar_chart(
    data: pd.Series,
    title: str,
    xlabel: str = "",
    ylabel: str = "",
    horizontal: bool = True,
    color_by_value: bool = False
):
    """
    Render a bar chart.

    Args:
        data: Series with values to plot
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        horizontal: If True, render horizontal bars
        color_by_value: If True, color bars by value (red/orange/green)
    """
    fig, ax = plt.subplots(figsize=(10, 6))

    if color_by_value:
        colors = [
            '#e74c3c' if v >= 20 else '#f39c12' if v >= 10 else '#2ecc71'
            for v in data.values
        ]
    else:
        colors = '#3498db'

    if horizontal:
        bars = ax.barh(data.index, data.values, color=colors)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
    else:
        bars = ax.bar(data.index, data.values, color=colors)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        plt.xticks(rotation=45, ha='right')

    ax.set_title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()

    st.pyplot(fig)
    plt.close()


def render_line_chart(
    data: pd.Series,
    title: str,
    xlabel: str = "",
    ylabel: str = "",
    highlight_range: tuple = None
):
    """
    Render a line chart.

    Args:
        data: Series with values to plot
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        highlight_range: Optional tuple (start_idx, end_idx) to highlight
    """
    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        range(len(data)),
        data.values,
        marker='o',
        linewidth=2,
        markersize=6,
        color='#2c3e50'
    )

    if highlight_range:
        start, end = highlight_range
        ax.axvspan(start, end, alpha=0.2, color='#3498db', label='Rainy Season')
        ax.legend()

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=14, fontweight='bold')

    ax.set_xticks(range(len(data)))
    ax.set_xticklabels(data.index, rotation=45, ha='right')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_category_chart(df: pd.DataFrame, title: str):
    """
    Render stockout rate by category chart.

    Args:
        df: DataFrame with category data
        title: Chart title
    """
    cat_data = df.groupby('medicine_category')['stockout'].mean() * 100
    cat_data = cat_data.sort_values(ascending=True)

    render_bar_chart(
        cat_data,
        title=title,
        xlabel="Stockout Rate (%)",
        horizontal=True,
        color_by_value=True
    )


def render_monthly_trend(df: pd.DataFrame, title: str):
    """
    Render monthly stockout trend with rainy season highlighting.

    Args:
        df: DataFrame with monthly data
        title: Chart title
    """
    monthly_data = df.groupby('month')['stockout'].mean() * 100

    fig, ax = plt.subplots(figsize=(12, 5))

    ax.plot(
        range(len(monthly_data)),
        monthly_data.values,
        marker='o',
        linewidth=2,
        markersize=6,
        color='#2c3e50'
    )

    # Highlight rainy season months (June-November)
    rainy_months = df.groupby('month')['is_rainy_season'].first()
    for i, (month, is_rainy) in enumerate(rainy_months.items()):
        if is_rainy:
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.2, color='#3498db')

    ax.set_xlabel('Month')
    ax.set_ylabel('Stockout Rate (%)')
    ax.set_title(title, fontsize=14, fontweight='bold')

    ax.set_xticks(range(0, len(monthly_data), 6))
    ax.set_xticklabels(monthly_data.index[::6], rotation=45, ha='right')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()
