"""
Medicine Stockout Prediction - Main Application Entry Point.

Run with: streamlit run app.py
"""
import streamlit as st
import config
from src.data.loader import load_data
from src.models.predictor import load_model
from src.components.sidebar import render_sidebar
from src.pages.risk_dashboard import render_risk_dashboard
from src.pages.stock_overview import render_stock_overview
from src.pages.predict import render_predict


# Page configuration
st.set_page_config(
    page_title=config.APP_NAME,
    page_icon=config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)


def main():
    """Main application entry point."""
    # Load data and model
    df = load_data()
    model, le, features = load_model()

    # Render sidebar and get selected page
    page = render_sidebar()

    # Route to selected page
    if page == "Risk Dashboard":
        render_risk_dashboard(df, model, le, features)
    elif page == "Stock Overview":
        render_stock_overview(df, model, le, features)
    elif page == "Predict":
        render_predict(df, model, le, features)


if __name__ == "__main__":
    main()
