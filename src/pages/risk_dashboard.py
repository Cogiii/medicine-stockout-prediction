"""
Risk Dashboard - Main landing page with Risk-First view and forecasts.
"""
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, timedelta
from src.utils.icons import get_icon
from src.components.metrics import render_risk_metrics
from src.components.tables import render_risk_table
from src.data.loader import get_latest_month_data
from src.models.predictor import predict_batch


def render_risk_dashboard(df: pd.DataFrame, model, le, features: list):
    """
    Render the Risk Dashboard page.

    Args:
        df: Full inventory DataFrame
        model: Trained model
        le: Label encoder
        features: Feature list
    """
    st.header("Risk Dashboard", anchor=False)
    st.caption("Risk alerts and forecasts")

    # Help text for first-time users
    with st.expander("What do the risk levels mean?", expanded=False):
        st.markdown("""
        **Risk levels show how likely a medicine is to run out of stock:**

        - **High Risk** - Likely to run out within **7 days**. Order immediately.
        - **Moderate Risk** - May run out within **7-14 days**. Plan to reorder soon.
        - **Low Risk** - Enough stock for **14+ days**. No immediate action needed.

        Risk is calculated based on current stock, daily usage patterns, and delivery schedules.
        """)

    # Get latest month data with predictions
    latest_df = get_latest_month_data(df)
    pred_df = predict_batch(model, le, features, latest_df)

    # Calculate risk counts
    high_count = (pred_df['risk_level'] == 'HIGH').sum()
    medium_count = (pred_df['risk_level'] == 'MEDIUM').sum()
    low_count = (pred_df['risk_level'] == 'LOW').sum()
    total = len(pred_df)

    # Risk summary metrics
    render_risk_metrics(high_count, medium_count, low_count, total)

    st.divider()

    # Filters
    st.subheader("Filters", anchor=False)
    col1, col2, col3 = st.columns(3)

    with col1:
        risk_options = {
            'High Risk': 'HIGH',
            'Moderate Risk': 'MEDIUM',
            'Low Risk': 'LOW'
        }
        selected_risks = st.multiselect(
            "Risk Level",
            options=list(risk_options.keys()),
            default=['High Risk', 'Moderate Risk']
        )
        risk_filter = [risk_options[r] for r in selected_risks]

    with col2:
        clinic_options = ['All'] + sorted(pred_df['clinic_name'].unique().tolist())
        clinic_filter = st.selectbox("Clinic", options=clinic_options)

    with col3:
        category_options = ['All'] + sorted(pred_df['medicine_category'].unique().tolist())
        category_filter = st.selectbox("Category", options=category_options)

    # Apply filters
    filtered_df = pred_df.copy()

    if risk_filter:
        filtered_df = filtered_df[filtered_df['risk_level'].isin(risk_filter)]

    if clinic_filter != 'All':
        filtered_df = filtered_df[filtered_df['clinic_name'] == clinic_filter]

    if category_filter != 'All':
        filtered_df = filtered_df[filtered_df['medicine_category'] == category_filter]

    st.divider()

    # Results header with count and download
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Risk Alerts ({len(filtered_df)} items)", anchor=False)
    with col2:
        csv_data = _prepare_download(filtered_df)
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="risk_alerts.csv",
            mime="text/csv",
            icon=get_icon("download"),
            use_container_width=True
        )

    # Risk table
    if len(filtered_df) > 0:
        render_risk_table(filtered_df, height=400)
    else:
        st.info("No items match the selected filters.")

    st.divider()

    # Forecasts Section
    st.subheader(f"{get_icon('timeline')} Forecasts", anchor=False)

    # Date range filter
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "From",
            value=date.today(),
            min_value=date.today(),
            max_value=date.today() + timedelta(days=365)
        )
    with col2:
        end_date = st.date_input(
            "To",
            value=date.today() + timedelta(days=365),
            min_value=start_date + timedelta(days=30),
            max_value=date.today() + timedelta(days=730)
        )

    # Risk Trend
    with st.expander("Risk Forecast Trend", expanded=True):
        _render_future_trend_chart(df, model, le, features, start_date, end_date)


def _prepare_download(df: pd.DataFrame) -> str:
    """Prepare CSV download data."""
    download_df = df[[
        'clinic_name', 'medicine_name', 'medicine_category',
        'stockout_probability', 'risk_level', 'days_until_stockout',
        'ending_stock', 'reorder_urgency', 'reorder_action'
    ]].copy()

    download_df.columns = [
        'Clinic', 'Medicine', 'Category', 'Risk Score', 'Risk Level',
        'Days Until Stockout', 'Current Stock', 'Reorder Urgency', 'Reorder Action'
    ]

    download_df['Risk Score'] = (download_df['Risk Score'] * 100).round(1).astype(str) + '%'

    return download_df.to_csv(index=False).encode('utf-8')


def _render_future_trend_chart(df: pd.DataFrame, model, le, features: list,
                                start_date: date, end_date: date):
    """Render future trend chart for given date range."""
    # Calculate number of months between dates
    months_diff = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month) + 1
    months_diff = max(1, min(months_diff, 24))  # Limit to 1-24 months

    trend_data = []

    for i in range(months_diff):
        future_month = ((start_date.month - 1 + i) % 12) + 1
        future_year = start_date.year + ((start_date.month - 1 + i) // 12)

        latest_df = get_latest_month_data(df).copy()
        latest_df['month_num'] = future_month

        pred_df = predict_batch(model, le, features, latest_df)

        avg_risk = pred_df['stockout_probability'].mean() * 100
        high_count = (pred_df['risk_level'] == 'HIGH').sum()

        month_name = date(future_year, future_month, 1).strftime('%b %Y')

        trend_data.append({
            'month': month_name,
            'risk': avg_risk,
            'high_risk_count': high_count
        })

    trend_df = pd.DataFrame(trend_data)

    fig, ax = plt.subplots(figsize=(12, 4))

    ax.plot(
        range(len(trend_df)),
        trend_df['risk'].values,
        marker='o',
        linewidth=2.5,
        markersize=8,
        color='#2c3e50',
        label='Predicted Risk'
    )

    ax.fill_between(
        range(len(trend_df)),
        trend_df['risk'].values,
        alpha=0.2,
        color='#3498db'
    )

    ax.axhline(y=30, color='#f39c12', linestyle='--', alpha=0.7, label='Moderate (30%)')
    ax.axhline(y=60, color='#e74c3c', linestyle='--', alpha=0.7, label='High Risk (60%)')

    ax.set_xlabel('Month', fontsize=10)
    ax.set_ylabel('Average Risk (%)', fontsize=10)
    ax.set_title(f'Predicted Stockout Risk: {start_date.strftime("%b %Y")} - {end_date.strftime("%b %Y")}',
                 fontsize=11, fontweight='bold')

    ax.set_xticks(range(len(trend_df)))
    ax.set_xticklabels(trend_df['month'], rotation=45, ha='right', fontsize=9)

    ax.set_ylim(0, max(trend_df['risk'].max() * 1.2, 40))
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    peak_month = trend_df.loc[trend_df['risk'].idxmax()]
    low_month = trend_df.loc[trend_df['risk'].idxmin()]

    col1, col2 = st.columns(2)
    with col1:
        st.caption(f"**Highest Risk:** {peak_month['month']} ({peak_month['risk']:.1f}%)")
    with col2:
        st.caption(f"**Lowest Risk:** {low_month['month']} ({low_month['risk']:.1f}%)")
