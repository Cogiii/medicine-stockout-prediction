"""
Predict - Smart stock simulation with variable consumption rates.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from datetime import date, timedelta
from src.utils.icons import get_icon
from src.utils.reorder import get_urgency_color
from src.models.predictor import predict_stockout


# Seasonal multipliers (rainy season: Jun-Nov)
SEASONAL_MULTIPLIERS = {
    'Antibiotic': 1.4,
    'ORS': 1.4,
    'Respiratory': 1.2,
}


def get_latest_record(df: pd.DataFrame, clinic: str, medicine: str) -> dict | None:
    """Get the most recent record for a clinic/medicine combination."""
    filtered = df[(df['clinic_name'] == clinic) & (df['medicine_name'] == medicine)]
    if filtered.empty:
        return None
    return filtered.sort_values('month', ascending=False).iloc[0].to_dict()


def get_historical_daily_rate(df: pd.DataFrame, clinic: str, medicine: str) -> tuple:
    """
    Calculate average daily consumption rate from historical data.

    Returns:
        Tuple of (average_rate, min_rate, max_rate)
    """
    history = df[(df['clinic_name'] == clinic) & (df['medicine_name'] == medicine)]
    if history.empty:
        return 2.0, 1.0, 3.0

    rates = history['consumption_rate']
    return rates.mean(), rates.min(), rates.max()


def get_seasonal_multiplier(day_from_today: int, category: str) -> float:
    """
    Get consumption multiplier based on season and medicine category.

    Args:
        day_from_today: Number of days from today
        category: Medicine category

    Returns:
        Multiplier (1.0 for dry season, higher for rainy season antibiotics/ORS)
    """
    future_date = date.today() + timedelta(days=day_from_today)
    is_rainy = 6 <= future_date.month <= 11

    if not is_rainy:
        return 1.0

    return SEASONAL_MULTIPLIERS.get(category, 1.0)


def project_stock_smart(
    current_stock: float,
    base_daily_rate: float,
    days: int,
    category: str,
    restock_events: list = None
) -> pd.DataFrame:
    """
    Project stock with variable daily rates based on season.

    Args:
        current_stock: Starting stock
        base_daily_rate: Base daily consumption (dry season)
        days: Number of days to project
        category: Medicine category
        restock_events: List of (day, quantity) tuples

    Returns:
        DataFrame with day, stock, daily_rate, restock columns
    """
    projection = []
    stock = float(current_stock)
    restock_dict = dict(restock_events) if restock_events else {}

    for day in range(days + 1):
        # Add restock if scheduled
        if day in restock_dict:
            stock += restock_dict[day]

        # Get seasonal multiplier for this day
        multiplier = get_seasonal_multiplier(day, category)
        daily_rate = base_daily_rate * multiplier

        projection.append({
            'day': day,
            'stock': max(0, stock),
            'daily_rate': daily_rate,
            'multiplier': multiplier,
            'restock': day in restock_dict
        })

        stock -= daily_rate

    return pd.DataFrame(projection)


def render_stock_timeline(
    projection: pd.DataFrame,
    base_daily_rate: float,
    delivery_day: int = None
):
    """Render stock projection chart with variable rates."""
    fig, ax1 = plt.subplots(figsize=(10, 4))

    # Calculate thresholds based on average rate
    avg_rate = projection['daily_rate'].mean()
    critical_threshold = 7 * avg_rate
    warning_threshold = 14 * avg_rate
    max_stock = max(projection['stock'].max() * 1.1, warning_threshold * 1.5)

    # Danger zones
    ax1.axhspan(0, critical_threshold, alpha=0.15, color='#e74c3c',
                label='Critical: < 7 days')
    ax1.axhspan(critical_threshold, warning_threshold, alpha=0.15, color='#f39c12',
                label='Warning: 7-14 days')

    # Stock line
    days = projection['day'].values
    stocks = projection['stock'].values

    ax1.plot(days, stocks, linewidth=2.5, color='#2c3e50')
    ax1.fill_between(days, stocks, alpha=0.2, color='#3498db')

    # Restock events
    restock_points = projection[projection['restock']]
    if not restock_points.empty:
        ax1.scatter(restock_points['day'], restock_points['stock'],
                    s=80, color='#27ae60', marker='^', zorder=5,
                    label='Delivery')

    # Stockout marker
    stockout_rows = projection[projection['stock'] <= 0]
    if not stockout_rows.empty:
        stockout_day = stockout_rows.iloc[0]['day']
        ax1.axvline(x=stockout_day, color='#e74c3c', linestyle='--',
                    linewidth=2, label=f'Stockout: Day {int(stockout_day)}')

    # Delivery marker
    if delivery_day and delivery_day <= projection['day'].max():
        ax1.axvline(x=delivery_day, color='#27ae60', linestyle='--',
                    linewidth=2, label=f'Delivery: Day {delivery_day}')

    ax1.set_xlabel('Days from Today', fontsize=10)
    ax1.set_ylabel('Stock (Units)', fontsize=10)
    ax1.set_xlim(0, projection['day'].max())
    ax1.set_ylim(0, max_stock)
    ax1.legend(loc='upper right', fontsize=8)
    ax1.grid(True, alpha=0.3)

    # Secondary axis for daily rate
    ax2 = ax1.twinx()
    ax2.plot(projection['day'], projection['daily_rate'],
             color='#9b59b6', linestyle=':', alpha=0.7, linewidth=1.5)
    ax2.set_ylabel('Daily Usage', fontsize=9, color='#9b59b6')
    ax2.tick_params(axis='y', labelcolor='#9b59b6')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def render_usage_history(df: pd.DataFrame, clinic: str, medicine: str):
    """Show historical monthly usage pattern."""
    history = df[(df['clinic_name'] == clinic) &
                 (df['medicine_name'] == medicine)].copy()

    if history.empty:
        st.caption("No historical data available")
        return

    history = history.sort_values('month').tail(24)  # Last 24 months

    fig, ax = plt.subplots(figsize=(10, 2.5))

    # Color by season
    colors = ['#27ae60' if r['is_rainy_season'] else '#3498db'
              for _, r in history.iterrows()]

    bars = ax.bar(range(len(history)), history['quantity_dispensed'], color=colors)

    # X-axis labels (show every 6 months)
    tick_positions = range(0, len(history), 6)
    tick_labels = [history.iloc[i]['month'] for i in tick_positions if i < len(history)]
    ax.set_xticks(list(tick_positions)[:len(tick_labels)])
    ax.set_xticklabels(tick_labels, rotation=45, ha='right', fontsize=8)

    ax.set_ylabel('Units', fontsize=9)
    ax.set_title('Monthly Usage History (Green = Rainy Season)', fontsize=10)
    ax.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    st.pyplot(fig)
    plt.close()


def get_stockout_risk_label(risk_level: str) -> str:
    """Convert technical risk level to user-friendly label."""
    return {
        'HIGH': 'High Risk of Stockout',
        'MEDIUM': 'Moderate Risk',
        'LOW': 'Low Risk'
    }.get(risk_level, risk_level)


def get_urgency_label(urgency: str) -> str:
    """Convert technical urgency to user-friendly label."""
    return {
        'IMMEDIATE': 'Order Now',
        'SOON': 'Order This Week',
        'SCHEDULED': 'Order Within 2-3 Weeks',
        'OK': 'No Order Needed'
    }.get(urgency, urgency)


def render_predict(df: pd.DataFrame, model, le, features: list):
    """Render the smart prediction page with variable consumption rates."""
    st.header(f"{get_icon('predict')} Medicine Stock Forecast", anchor=False)

    # Initialize session state
    if 'scenarios' not in st.session_state:
        st.session_state.scenarios = []
    if 'restock_events' not in st.session_state:
        st.session_state.restock_events = []

    # Layout: Results (Left) | Settings (Right)
    results_col, settings_col = st.columns([3, 2])

    # ==================== SETTINGS PANEL (Right) ====================
    with settings_col:
        with st.container(border=True):
            st.subheader(f"{get_icon('settings')} Settings", anchor=False)

            # Clinic Selection
            clinic_options = df.drop_duplicates('clinic_name')[
                ['clinic_name', 'remoteness_score', 'population_served']
            ]
            selected_clinic = st.selectbox(
                "Rural Health Unit (RHU)",
                options=clinic_options['clinic_name'].tolist(),
                key="predict_clinic"
            )
            clinic_data = clinic_options[
                clinic_options['clinic_name'] == selected_clinic
            ].iloc[0]

            # Medicine Selection
            medicine_options = df.drop_duplicates('medicine_name')[
                ['medicine_name', 'medicine_category']
            ]
            selected_medicine = st.selectbox(
                "Medicine",
                options=medicine_options['medicine_name'].tolist(),
                key="predict_medicine"
            )
            med_data = medicine_options[
                medicine_options['medicine_name'] == selected_medicine
            ].iloc[0]
            category = med_data['medicine_category']

            # Auto-load real data
            latest_record = get_latest_record(df, selected_clinic, selected_medicine)
            real_data = latest_record or {}

            # Auto-calculate daily rate from history
            avg_rate, min_rate, max_rate = get_historical_daily_rate(
                df, selected_clinic, selected_medicine
            )

            if latest_record:
                st.caption(f"{get_icon('info')} Data from: **{latest_record['month']}**")

            st.divider()

            # Stock Information
            st.markdown(f"**{get_icon('inventory')} Stock Information**")

            current_stock = st.number_input(
                "Stock on Hand (units)",
                min_value=0,
                value=int(real_data.get('ending_stock', 100)),
                step=1,
                help="Current available units"
            )

            # Show calculated daily usage (not editable)
            st.caption(f"**Daily Usage (auto-calculated):** {avg_rate:.1f} units/day")
            st.caption(f"Range: {min_rate:.1f} - {max_rate:.1f} units/day")

            patient_visits = st.number_input(
                "Monthly Patient Visits",
                min_value=0,
                value=int(real_data.get('patient_visits', 80)),
                step=1
            )

            st.divider()

            # Delivery Information
            st.markdown(f"**{get_icon('calendar')} Delivery Schedule**")

            last_delivery = st.date_input(
                "Last Delivery Received",
                value=date.today() - timedelta(days=int(real_data.get('days_since_last_delivery', 15))),
                max_value=date.today()
            )
            days_since_delivery = (date.today() - last_delivery).days

            expected_delivery = st.date_input(
                "Next Expected Delivery",
                value=date.today() + timedelta(days=14),
                min_value=date.today()
            )
            days_until_delivery = (expected_delivery - date.today()).days

            st.caption(f"Last: **{days_since_delivery} days ago** • Next: **{days_until_delivery} days**")

            st.divider()

            # Forecast Settings
            st.markdown(f"**{get_icon('simulation')} Forecast Period**")

            simulation_days = st.number_input(
                "Days to Forecast",
                min_value=7,
                value=90,
                step=1
            )

            current_month = date.today().month
            is_rainy = 1 if 6 <= current_month <= 11 else 0

            st.divider()

            # Planned Deliveries
            st.markdown(f"**{get_icon('add')} Planned Deliveries**")

            with st.expander("Add Delivery", expanded=False):
                restock_day = st.number_input(
                    "Arrives on Day",
                    min_value=1,
                    value=days_until_delivery,
                    step=1
                )
                restock_qty = st.number_input(
                    "Quantity (units)",
                    min_value=1,
                    value=int(real_data.get('quantity_received', 50)) if real_data.get('quantity_received', 0) > 0 else 50,
                    step=1
                )

                col_a, col_b = st.columns(2)
                with col_a:
                    if st.button("Add", icon=get_icon("add"), use_container_width=True):
                        st.session_state.restock_events.append((restock_day, restock_qty))
                        st.rerun()
                with col_b:
                    if st.button("Clear", icon=get_icon("clear"), use_container_width=True):
                        st.session_state.restock_events = []
                        st.rerun()

            if st.session_state.restock_events:
                for day, qty in st.session_state.restock_events:
                    st.caption(f"• Day {day}: +{qty} units")

    # ==================== RESULTS (Left) ====================
    with results_col:
        # Smart projection with variable rates
        projection = project_stock_smart(
            current_stock=current_stock,
            base_daily_rate=avg_rate,
            days=simulation_days,
            category=category,
            restock_events=st.session_state.restock_events
        )

        # Calculate stockout day
        stockout_rows = projection[projection['stock'] <= 0]
        days_until_stockout = int(stockout_rows.iloc[0]['day']) if not stockout_rows.empty else simulation_days

        # Build prediction input
        quantity_dispensed = int(avg_rate * 30)
        ending_stock = max(0, current_stock)
        stock_to_consumption_ratio = ending_stock / max(1, quantity_dispensed)

        input_data = {
            'remoteness_score': clinic_data['remoteness_score'],
            'population_served': clinic_data['population_served'],
            'medicine_category': category,
            'month_num': current_month,
            'is_rainy_season': is_rainy,
            'beginning_stock': current_stock,
            'quantity_received': 0,
            'quantity_dispensed': quantity_dispensed,
            'patient_visits': patient_visits,
            'days_since_last_delivery': days_since_delivery,
            'consumption_rate': avg_rate,
            'stock_to_consumption_ratio': stock_to_consumption_ratio,
            'rolling_avg_consumption': quantity_dispensed,
            'prev_month_stockout': 0
        }

        result = predict_stockout(model, le, features, input_data)
        reorder = result['reorder']

        # Key Metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            probability_pct = result['probability'] * 100
            st.metric("Chance of Running Out", f"{probability_pct:.0f}%")

        with col2:
            if days_until_stockout >= simulation_days:
                st.metric("Stock Will Last", f"{simulation_days}+ days")
            else:
                st.metric("Stock Will Last", f"{days_until_stockout} days")

        with col3:
            st.metric("Stock on Hand", f"{current_stock} units")

        # Risk Alert
        risk_level = result['risk_level']
        risk_label = get_stockout_risk_label(risk_level)
        urgency_label = get_urgency_label(reorder.urgency)

        if risk_level == 'HIGH':
            st.error(f"**{risk_label}** — {urgency_label}")
        elif risk_level == 'MEDIUM':
            st.warning(f"**{risk_label}** — {urgency_label}")
        else:
            st.success(f"**{risk_label}** — {urgency_label}")

        if reorder.suggested_quantity > 0:
            st.info(f"**Recommended Order:** {reorder.suggested_quantity} units • {reorder.reason}")

        # Stock Forecast Chart
        st.markdown("##### Stock Level Forecast")
        render_stock_timeline(
            projection=projection,
            base_daily_rate=avg_rate,
            delivery_day=days_until_delivery if days_until_delivery <= simulation_days else None
        )

        # Clinic Info
        remoteness = clinic_data['remoteness_score']
        if remoteness <= 0.3:
            location_desc = "Easy to Reach"
        elif remoteness <= 0.5:
            location_desc = "Moderate Access"
        elif remoteness <= 0.7:
            location_desc = "Hard to Reach"
        else:
            location_desc = "Very Hard to Reach"
        st.caption(
            f"**{selected_clinic}** • {selected_medicine} ({category}) • "
            f"Location: {location_desc} • Population: {int(clinic_data['population_served']):,}"
        )

    # ==================== SCENARIO COMPARISON ====================
    st.divider()

    with st.expander(f"{get_icon('compare')} Compare Scenarios", expanded=False):
        st.caption("Save scenarios to compare different situations")

        col1, col2 = st.columns([3, 1])
        with col1:
            scenario_name = st.text_input(
                "Scenario Name",
                value=f"Scenario {len(st.session_state.scenarios) + 1}",
                label_visibility="collapsed",
                placeholder="Name this scenario..."
            )
        with col2:
            if st.button("Save Scenario", icon=get_icon("save"), use_container_width=True):
                st.session_state.scenarios.append({
                    'Scenario': scenario_name,
                    'Clinic': selected_clinic.split()[0],
                    'Medicine': selected_medicine.split()[0],
                    'Stock': current_stock,
                    'Avg Usage': f"{avg_rate:.1f}",
                    'Days Left': days_until_stockout if days_until_stockout < simulation_days else f"{simulation_days}+",
                    'Risk': get_stockout_risk_label(result['risk_level']),
                    'Action': get_urgency_label(reorder.urgency)
                })
                st.rerun()

        if st.session_state.scenarios:
            scenarios_df = pd.DataFrame(st.session_state.scenarios)

            def style_risk(val):
                if 'High' in str(val):
                    return 'color: #c0392b; font-weight: bold'
                elif 'Moderate' in str(val):
                    return 'color: #d68910; font-weight: bold'
                return 'color: #27ae60; font-weight: bold'

            def style_action(val):
                if 'Now' in str(val):
                    return 'color: #c0392b; font-weight: bold'
                elif 'Week' in str(val):
                    return 'color: #d68910'
                elif 'Weeks' in str(val):
                    return 'color: #2874a6'
                return 'color: #27ae60'

            styled_df = scenarios_df.style.map(
                style_risk, subset=['Risk']
            ).map(
                style_action, subset=['Action']
            )

            st.dataframe(styled_df, use_container_width=True, hide_index=True)

            if st.button("Clear All Scenarios", icon=get_icon("clear")):
                st.session_state.scenarios = []
                st.rerun()
