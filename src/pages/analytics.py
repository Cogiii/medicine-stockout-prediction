"""
Analytics - Historical trends and predictive forecasts.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, timedelta
from src.utils.icons import get_icon
from src.components.charts import render_bar_chart, render_category_chart
from src.models.predictor import predict_batch
from src.data.loader import get_latest_month_data


# Seasonal multipliers (same as predict.py)
SEASONAL_MULTIPLIERS = {
    'Antibiotic': 1.4,
    'ORS': 1.4,
    'Respiratory': 1.2,
}


def render_analytics(df: pd.DataFrame, model=None, le=None, features: list = None):
    """
    Render the Analytics page with historical and predictive analysis.

    Args:
        df: Full inventory DataFrame
        model: Trained model (optional, for forecasts)
        le: Label encoder (optional, for forecasts)
        features: Feature list (optional, for forecasts)
    """
    st.header(f"{get_icon('analytics')} Analytics", anchor=False)
    st.caption("Predictive forecasts and stockout analysis")

    # Tabs - Forecasts + By Clinic + By Medicine
    if model is not None:
        tab1, tab2, tab3 = st.tabs([
            "Forecasts",
            "By Clinic",
            "By Medicine"
        ])

        with tab1:
            _render_forecasts_tab(df, model, le, features)

        with tab2:
            _render_clinic_tab(df)

        with tab3:
            _render_medicine_tab(df)
    else:
        tab1, tab2 = st.tabs([
            "By Clinic",
            "By Medicine"
        ])

        with tab1:
            _render_clinic_tab(df)

        with tab2:
            _render_medicine_tab(df)


def _render_forecasts_tab(df: pd.DataFrame, model, le, features: list):
    """Render predictive forecasts tab."""

    # Get latest data with predictions
    latest_df = get_latest_month_data(df)
    pred_df = predict_batch(model, le, features, latest_df)

    # Current month info
    current_month = date.today().month
    current_year = date.today().year
    is_rainy = 6 <= current_month <= 11

    st.subheader("Risk Forecast Summary", anchor=False)

    # High-level forecast metrics
    col1, col2, col3, col4 = st.columns(4)

    high_risk_count = (pred_df['risk_level'] == 'HIGH').sum()
    medium_risk_count = (pred_df['risk_level'] == 'MEDIUM').sum()
    total_items = len(pred_df)

    with col1:
        st.metric(
            "High Risk Items",
            high_risk_count,
            help="Items with >60% chance of stockout"
        )

    with col2:
        st.metric(
            "Moderate Risk Items",
            medium_risk_count,
            help="Items with 30-60% chance of stockout"
        )

    with col3:
        avg_risk = pred_df['stockout_probability'].mean() * 100
        st.metric(
            "Average Risk Score",
            f"{avg_risk:.1f}%"
        )

    with col4:
        # Seasonal indicator
        if is_rainy:
            st.metric("Season", "Rainy", help="Higher demand for antibiotics & ORS")
        else:
            st.metric("Season", "Dry", help="Normal demand patterns")

    st.divider()

    # Future Trend Chart (like historical but for predictions)
    st.subheader("12-Month Risk Forecast Trend", anchor=False)
    st.caption("Predicted average stockout risk for the next 12 months")
    _render_future_trend_chart(df, model, le, features)

    st.divider()

    # 3-Month Forecast Table
    st.subheader("3-Month Risk Projection", anchor=False)
    _render_monthly_forecast(df, model, le, features)

    st.divider()

    # Risk Heatmap
    st.subheader("Clinic Risk Heatmap", anchor=False)
    st.caption("Predicted stockout risk by clinic (next 3 months)")
    _render_risk_heatmap(df, model, le, features)

    st.divider()

    # Top Risk Items
    st.subheader("Highest Risk Items", anchor=False)
    _render_top_risk_items(pred_df)

    st.divider()

    # Seasonal Impact Forecast
    st.subheader("Seasonal Impact Forecast", anchor=False)
    _render_seasonal_forecast(df, model, le, features)


def _render_future_trend_chart(df: pd.DataFrame, model, le, features: list):
    """Render 12-month future trend chart similar to historical trend."""
    current_month = date.today().month
    current_year = date.today().year

    trend_data = []

    for i in range(12):
        # Calculate future month
        future_month = ((current_month - 1 + i) % 12) + 1
        future_year = current_year + ((current_month - 1 + i) // 12)
        is_rainy = 6 <= future_month <= 11

        # Get latest data as base
        latest_df = get_latest_month_data(df).copy()

        # Adjust for future month
        latest_df['month_num'] = future_month
        latest_df['is_rainy_season'] = int(is_rainy)

        # Adjust consumption for seasonal patterns
        for category, mult in SEASONAL_MULTIPLIERS.items():
            mask = latest_df['medicine_category'] == category
            if is_rainy:
                latest_df.loc[mask, 'quantity_dispensed'] = (
                    latest_df.loc[mask, 'quantity_dispensed'] * mult
                ).astype(int)
                latest_df.loc[mask, 'consumption_rate'] = (
                    latest_df.loc[mask, 'consumption_rate'] * mult
                )

        # Predict
        pred_df = predict_batch(model, le, features, latest_df)

        avg_risk = pred_df['stockout_probability'].mean() * 100
        high_count = (pred_df['risk_level'] == 'HIGH').sum()

        month_name = date(future_year, future_month, 1).strftime('%b %Y')

        trend_data.append({
            'month': month_name,
            'month_num': future_month,
            'risk': avg_risk,
            'high_risk_count': high_count,
            'is_rainy': is_rainy
        })

    trend_df = pd.DataFrame(trend_data)

    # Create the chart
    fig, ax = plt.subplots(figsize=(12, 5))

    # Plot the line
    ax.plot(
        range(len(trend_df)),
        trend_df['risk'].values,
        marker='o',
        linewidth=2.5,
        markersize=8,
        color='#2c3e50',
        label='Predicted Risk'
    )

    # Fill area under the line
    ax.fill_between(
        range(len(trend_df)),
        trend_df['risk'].values,
        alpha=0.2,
        color='#3498db'
    )

    # Highlight rainy season months
    for i, row in trend_df.iterrows():
        if row['is_rainy']:
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.15, color='#27ae60')

    # Add threshold lines
    ax.axhline(y=30, color='#f39c12', linestyle='--', alpha=0.7, label='Moderate Threshold (30%)')
    ax.axhline(y=60, color='#e74c3c', linestyle='--', alpha=0.7, label='High Risk Threshold (60%)')

    # Labels and styling
    ax.set_xlabel('Month', fontsize=10)
    ax.set_ylabel('Average Stockout Risk (%)', fontsize=10)
    ax.set_title('Predicted Stockout Risk Trend (Green = Rainy Season)', fontsize=12, fontweight='bold')

    ax.set_xticks(range(len(trend_df)))
    ax.set_xticklabels(trend_df['month'], rotation=45, ha='right', fontsize=9)

    ax.set_ylim(0, max(trend_df['risk'].max() * 1.2, 40))
    ax.legend(loc='upper right', fontsize=8)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    # Show peak risk months
    peak_month = trend_df.loc[trend_df['risk'].idxmax()]
    low_month = trend_df.loc[trend_df['risk'].idxmin()]

    col1, col2 = st.columns(2)
    with col1:
        st.caption(
            f"**Highest Risk:** {peak_month['month']} ({peak_month['risk']:.1f}%) — "
            f"{'Rainy season' if peak_month['is_rainy'] else 'Dry season'}"
        )
    with col2:
        st.caption(
            f"**Lowest Risk:** {low_month['month']} ({low_month['risk']:.1f}%) — "
            f"{'Rainy season' if low_month['is_rainy'] else 'Dry season'}"
        )


def _render_monthly_forecast(df: pd.DataFrame, model, le, features: list):
    """Render 3-month ahead forecast."""
    current_month = date.today().month
    current_year = date.today().year

    forecast_data = []

    for i in range(3):
        # Calculate future month
        future_month = ((current_month - 1 + i) % 12) + 1
        future_year = current_year + ((current_month - 1 + i) // 12)
        is_rainy = 6 <= future_month <= 11

        # Get latest data as base
        latest_df = get_latest_month_data(df).copy()

        # Adjust for future month
        latest_df['month_num'] = future_month
        latest_df['is_rainy_season'] = int(is_rainy)

        # Adjust consumption for seasonal patterns
        for category, mult in SEASONAL_MULTIPLIERS.items():
            mask = latest_df['medicine_category'] == category
            if is_rainy:
                latest_df.loc[mask, 'quantity_dispensed'] = (
                    latest_df.loc[mask, 'quantity_dispensed'] * mult
                ).astype(int)
                latest_df.loc[mask, 'consumption_rate'] = (
                    latest_df.loc[mask, 'consumption_rate'] * mult
                )

        # Predict
        pred_df = predict_batch(model, le, features, latest_df)

        high_count = (pred_df['risk_level'] == 'HIGH').sum()
        med_count = (pred_df['risk_level'] == 'MEDIUM').sum()
        avg_prob = pred_df['stockout_probability'].mean() * 100

        month_name = date(future_year, future_month, 1).strftime('%b %Y')

        forecast_data.append({
            'Month': month_name,
            'High Risk': high_count,
            'Moderate Risk': med_count,
            'Avg Risk %': avg_prob,
            'Season': 'Rainy' if is_rainy else 'Dry'
        })

    forecast_df = pd.DataFrame(forecast_data)

    # Display as styled table
    def style_risk(val):
        if isinstance(val, (int, float)):
            if val >= 20:
                return 'background-color: #ffcccc'
            elif val >= 10:
                return 'background-color: #fff3cd'
        return ''

    def style_season(val):
        if val == 'Rainy':
            return 'background-color: #d4edda; color: #155724'
        return ''

    styled_df = forecast_df.style.applymap(
        style_risk, subset=['High Risk', 'Moderate Risk']
    ).applymap(
        style_season, subset=['Season']
    ).format({'Avg Risk %': '{:.1f}%'})

    st.dataframe(styled_df, use_container_width=True, hide_index=True)

    # Bar chart visualization
    fig, ax = plt.subplots(figsize=(10, 4))

    x = range(len(forecast_df))
    width = 0.35

    bars1 = ax.bar([i - width/2 for i in x], forecast_df['High Risk'],
                   width, label='High Risk', color='#e74c3c')
    bars2 = ax.bar([i + width/2 for i in x], forecast_df['Moderate Risk'],
                   width, label='Moderate Risk', color='#f39c12')

    ax.set_xlabel('Month')
    ax.set_ylabel('Number of Items')
    ax.set_title('Predicted Risk Items by Month')
    ax.set_xticks(x)
    ax.set_xticklabels(forecast_df['Month'])
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')

    # Add season indicators
    for i, row in forecast_df.iterrows():
        if row['Season'] == 'Rainy':
            ax.axvspan(i - 0.5, i + 0.5, alpha=0.1, color='green')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def _render_risk_heatmap(df: pd.DataFrame, model, le, features: list):
    """Render clinic x month risk heatmap."""
    current_month = date.today().month
    current_year = date.today().year

    clinics = df['clinic_name'].unique()
    heatmap_data = []

    for i in range(3):
        future_month = ((current_month - 1 + i) % 12) + 1
        future_year = current_year + ((current_month - 1 + i) // 12)
        is_rainy = 6 <= future_month <= 11
        month_name = date(future_year, future_month, 1).strftime('%b')

        latest_df = get_latest_month_data(df).copy()
        latest_df['month_num'] = future_month
        latest_df['is_rainy_season'] = int(is_rainy)

        # Adjust for season
        for category, mult in SEASONAL_MULTIPLIERS.items():
            mask = latest_df['medicine_category'] == category
            if is_rainy:
                latest_df.loc[mask, 'consumption_rate'] *= mult

        pred_df = predict_batch(model, le, features, latest_df)

        for clinic in clinics:
            clinic_data = pred_df[pred_df['clinic_name'] == clinic]
            avg_risk = clinic_data['stockout_probability'].mean() * 100
            heatmap_data.append({
                'Clinic': clinic.replace(' RHU', ''),
                'Month': month_name,
                'Risk': avg_risk
            })

    heatmap_df = pd.DataFrame(heatmap_data)
    pivot_df = heatmap_df.pivot(index='Clinic', columns='Month', values='Risk')

    # Reorder columns to chronological
    months_order = []
    for i in range(3):
        future_month = ((current_month - 1 + i) % 12) + 1
        future_year = current_year + ((current_month - 1 + i) // 12)
        months_order.append(date(future_year, future_month, 1).strftime('%b'))
    pivot_df = pivot_df[months_order]

    # Sort by average risk
    pivot_df['Avg'] = pivot_df.mean(axis=1)
    pivot_df = pivot_df.sort_values('Avg', ascending=False)
    pivot_df = pivot_df.drop('Avg', axis=1)

    # Create heatmap
    fig, ax = plt.subplots(figsize=(8, 6))

    im = ax.imshow(pivot_df.values, cmap='RdYlGn_r', aspect='auto',
                   vmin=0, vmax=50)

    ax.set_xticks(range(len(pivot_df.columns)))
    ax.set_xticklabels(pivot_df.columns)
    ax.set_yticks(range(len(pivot_df.index)))
    ax.set_yticklabels(pivot_df.index, fontsize=9)

    # Add text annotations
    for i in range(len(pivot_df.index)):
        for j in range(len(pivot_df.columns)):
            value = pivot_df.iloc[i, j]
            color = 'white' if value > 30 else 'black'
            ax.text(j, i, f'{value:.0f}%', ha='center', va='center',
                    color=color, fontsize=10)

    ax.set_title('Predicted Stockout Risk by Clinic (%)')
    plt.colorbar(im, ax=ax, label='Risk %')
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def _render_top_risk_items(pred_df: pd.DataFrame):
    """Render top risk items table."""
    top_risk = pred_df.nlargest(10, 'stockout_probability')[[
        'clinic_name', 'medicine_name', 'medicine_category',
        'stockout_probability', 'risk_level', 'ending_stock',
        'consumption_rate', 'days_until_stockout'
    ]].copy()

    top_risk.columns = [
        'Clinic', 'Medicine', 'Category', 'Risk Score',
        'Risk Level', 'Stock', 'Daily Usage', 'Days Left'
    ]

    top_risk['Risk Score'] = (top_risk['Risk Score'] * 100).round(1).astype(str) + '%'
    top_risk['Daily Usage'] = top_risk['Daily Usage'].round(1)

    def style_risk(val):
        if val == 'HIGH':
            return 'background-color: #ffcccc'
        elif val == 'MEDIUM':
            return 'background-color: #fff3cd'
        return 'background-color: #d4edda'

    styled_df = top_risk.style.applymap(style_risk, subset=['Risk Level'])

    st.dataframe(styled_df, use_container_width=True, hide_index=True)


def _render_seasonal_forecast(df: pd.DataFrame, model, le, features: list):
    """Render seasonal impact forecast."""
    current_month = date.today().month
    is_rainy = 6 <= current_month <= 11

    # Calculate impact by category
    latest_df = get_latest_month_data(df).copy()

    # Predict for dry season scenario
    latest_df['is_rainy_season'] = 0
    latest_df['month_num'] = 3  # March (dry)
    dry_pred = predict_batch(model, le, features, latest_df.copy())

    # Predict for rainy season scenario
    latest_df['is_rainy_season'] = 1
    latest_df['month_num'] = 8  # August (rainy)
    # Adjust consumption for affected categories
    for category, mult in SEASONAL_MULTIPLIERS.items():
        mask = latest_df['medicine_category'] == category
        latest_df.loc[mask, 'consumption_rate'] *= mult
        latest_df.loc[mask, 'quantity_dispensed'] = (
            latest_df.loc[mask, 'quantity_dispensed'] * mult
        ).astype(int)

    rainy_pred = predict_batch(model, le, features, latest_df)

    # Compare by category
    categories = df['medicine_category'].unique()
    comparison_data = []

    for cat in categories:
        dry_risk = dry_pred[dry_pred['medicine_category'] == cat]['stockout_probability'].mean() * 100
        rainy_risk = rainy_pred[rainy_pred['medicine_category'] == cat]['stockout_probability'].mean() * 100
        impact = rainy_risk - dry_risk

        comparison_data.append({
            'Category': cat,
            'Dry Season Risk': dry_risk,
            'Rainy Season Risk': rainy_risk,
            'Impact': impact
        })

    comparison_df = pd.DataFrame(comparison_data)
    comparison_df = comparison_df.sort_values('Impact', ascending=False)

    col1, col2 = st.columns([2, 3])

    with col1:
        st.markdown("**Seasonal Risk Change by Category**")

        def style_impact(val):
            if val > 5:
                return 'background-color: #ffcccc; color: #721c24'
            elif val > 2:
                return 'background-color: #fff3cd; color: #856404'
            return 'background-color: #d4edda; color: #155724'

        display_df = comparison_df.copy()
        display_df['Dry Season Risk'] = display_df['Dry Season Risk'].round(1).astype(str) + '%'
        display_df['Rainy Season Risk'] = display_df['Rainy Season Risk'].round(1).astype(str) + '%'
        display_df['Impact'] = display_df['Impact'].apply(lambda x: f'+{x:.1f}%' if x > 0 else f'{x:.1f}%')

        st.dataframe(display_df, use_container_width=True, hide_index=True)

    with col2:
        # Bar chart
        fig, ax = plt.subplots(figsize=(8, 4))

        x = range(len(comparison_df))
        width = 0.35

        ax.bar([i - width/2 for i in x], comparison_df['Dry Season Risk'],
               width, label='Dry Season', color='#f39c12')
        ax.bar([i + width/2 for i in x], comparison_df['Rainy Season Risk'],
               width, label='Rainy Season', color='#27ae60')

        ax.set_xlabel('Category')
        ax.set_ylabel('Average Risk (%)')
        ax.set_title('Seasonal Impact on Stockout Risk')
        ax.set_xticks(x)
        ax.set_xticklabels(comparison_df['Category'], rotation=45, ha='right', fontsize=8)
        ax.legend()
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        st.pyplot(fig)
        plt.close()

    # Insight box
    if is_rainy:
        st.info(
            f"{get_icon('rainy')} **Currently in Rainy Season** — "
            f"Antibiotics, ORS, and Respiratory medicines have higher demand. "
            f"Plan for {int(SEASONAL_MULTIPLIERS['Antibiotic'] * 100 - 100)}% more antibiotic stock."
        )
    else:
        months_to_rainy = (6 - current_month) if current_month < 6 else (18 - current_month)
        st.info(
            f"{get_icon('dry')} **Currently in Dry Season** — "
            f"Rainy season starts in {months_to_rainy} month(s). "
            f"Consider pre-ordering antibiotics and ORS supplies."
        )


def _render_clinic_tab(df: pd.DataFrame):
    """Render clinic analysis tab."""
    st.subheader("Stockout Rate by Clinic", anchor=False)

    clinic_data = df.groupby('clinic_name')['stockout'].mean() * 100
    clinic_data = clinic_data.sort_values(ascending=True)

    render_bar_chart(
        clinic_data,
        title="Historical Stockout Rate by Clinic",
        xlabel="Stockout Rate (%)",
        horizontal=True,
        color_by_value=True
    )

    # Remote vs Urban
    st.subheader("Remote vs Urban Clinics", anchor=False)

    col1, col2 = st.columns(2)

    urban_rate = df[df['remoteness_score'] <= 0.5]['stockout'].mean() * 100
    remote_rate = df[df['remoteness_score'] > 0.5]['stockout'].mean() * 100

    with col1:
        st.metric(f"{get_icon('clinic')} Urban Clinics", f"{urban_rate:.1f}%")

    with col2:
        delta = remote_rate - urban_rate
        st.metric(
            f"{get_icon('clinic')} Remote Clinics",
            f"{remote_rate:.1f}%",
            delta=f"{delta:+.1f}%"
        )


def _render_medicine_tab(df: pd.DataFrame):
    """Render medicine analysis tab."""
    st.subheader("Stockout Rate by Medicine", anchor=False)

    med_data = df.groupby('medicine_name')['stockout'].mean() * 100
    med_data = med_data.sort_values(ascending=True)

    render_bar_chart(
        med_data,
        title="Historical Stockout Rate by Medicine",
        xlabel="Stockout Rate (%)",
        horizontal=True
    )

    # By Category
    st.subheader("Stockout Rate by Category", anchor=False)

    render_category_chart(df, "Historical Stockout Rate by Medicine Category")
