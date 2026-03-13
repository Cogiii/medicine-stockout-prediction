"""
Stock Overview - RHU-centric stock view.
"""
import pandas as pd
import streamlit as st
from src.utils.icons import get_icon
from src.components.metrics import render_stock_metrics
from src.components.tables import render_stock_table
from src.data.loader import get_latest_month_data, get_medicine_summary, get_clinic_summary
from src.models.predictor import predict_batch


def _get_location_accessibility(score: float) -> str:
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


def render_stock_overview(df: pd.DataFrame, model, le, features: list):
    """
    Render the Stock Overview page.

    Args:
        df: Full inventory DataFrame
        model: Trained model
        le: Label encoder
        features: Feature list
    """
    st.header("Stock Overview", anchor=False)
    st.caption("Inventory levels by clinic")

    # Get latest data
    latest_df = get_latest_month_data(df)
    pred_df = predict_batch(model, le, features, latest_df)

    # Clinic selector
    clinics = sorted(pred_df['clinic_name'].unique().tolist())
    selected_clinic = st.selectbox(
        "Select Clinic",
        options=clinics,
        index=0
    )

    # Filter to selected clinic
    clinic_df = pred_df[pred_df['clinic_name'] == selected_clinic]

    st.divider()

    # Clinic info
    if len(clinic_df) > 0:
        clinic_info = clinic_df.iloc[0]

        # Metrics row
        total_stock = int(clinic_df['ending_stock'].sum())
        avg_days = clinic_df['days_until_stockout'].mean()

        # Calculate risk score (0-10 based on high risk percentage)
        high_risk_pct = (clinic_df['risk_level'] == 'HIGH').mean() * 100
        risk_score = min(10, high_risk_pct / 10)

        render_stock_metrics(total_stock, avg_days, risk_score)

        # Clinic details
        col1, col2 = st.columns(2)
        with col1:
            accessibility = _get_location_accessibility(clinic_info['remoteness_score'])
            st.metric("Location", accessibility)
        with col2:
            st.metric("Population Served", f"{int(clinic_info['population_served']):,}")

        st.divider()

        # Medicine inventory table
        st.subheader("Medicine Inventory", anchor=False)

        # Prepare display data
        display_df = clinic_df[[
            'medicine_name', 'medicine_category', 'ending_stock',
            'consumption_rate', 'days_until_stockout', 'risk_level',
            'reorder_urgency', 'reorder_action'
        ]].copy()

        display_df.columns = [
            'Medicine', 'Category', 'Stock', 'Daily Usage',
            'Days Left', 'Risk', 'Urgency', 'Action'
        ]

        # Convert risk levels to user-friendly labels
        display_df['Risk'] = display_df['Risk'].apply(_get_risk_label)

        # Sort by days left (ascending)
        display_df = display_df.sort_values('Days Left')

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400,
            column_config={
                "Stock": st.column_config.NumberColumn(format="%d"),
                "Daily Usage": st.column_config.NumberColumn(format="%.1f"),
                "Days Left": st.column_config.NumberColumn(format="%d")
            }
        )

    else:
        st.warning("No data available for selected clinic.")


def render_all_clinics_summary(df: pd.DataFrame):
    """
    Render summary of all clinics.

    Args:
        df: Full inventory DataFrame
    """
    st.subheader("All Clinics Summary", anchor=False)

    clinic_summary = get_clinic_summary(df)

    st.dataframe(
        clinic_summary,
        use_container_width=True,
        hide_index=True,
        column_config={
            "remoteness_score": st.column_config.NumberColumn(
                "Remoteness",
                format="%.2f"
            ),
            "population_served": st.column_config.NumberColumn(
                "Population",
                format="%d"
            ),
            "stockout_rate": st.column_config.NumberColumn(
                "Stockout %",
                format="%.1f%%"
            )
        }
    )
