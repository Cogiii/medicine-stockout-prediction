"""
Data loading functions.
"""
import pandas as pd
import streamlit as st
import config


@st.cache_data
def load_data() -> pd.DataFrame:
    """
    Load medicine inventory data from CSV.

    Returns:
        DataFrame with all inventory records
    """
    df = pd.read_csv(config.DATA_PATH)
    return df


def get_latest_month_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get data for the most recent month only.

    Args:
        df: Full inventory DataFrame

    Returns:
        DataFrame filtered to latest month
    """
    latest_month = df['month'].max()
    return df[df['month'] == latest_month].copy()


def get_clinic_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Get summary statistics by clinic.

    Args:
        df: Inventory DataFrame

    Returns:
        DataFrame with clinic-level aggregations
    """
    summary = df.groupby(['clinic_id', 'clinic_name', 'remoteness_score', 'population_served']).agg({
        'stockout': ['mean', 'sum'],
        'ending_stock': 'sum',
        'medicine_name': 'nunique'
    }).reset_index()

    summary.columns = [
        'clinic_id', 'clinic_name', 'remoteness_score', 'population_served',
        'stockout_rate', 'total_stockouts', 'total_stock', 'medicine_count'
    ]

    summary['stockout_rate'] = (summary['stockout_rate'] * 100).round(1)

    return summary


def get_medicine_summary(df: pd.DataFrame, clinic_id: int = None) -> pd.DataFrame:
    """
    Get summary statistics by medicine.

    Args:
        df: Inventory DataFrame
        clinic_id: Optional clinic ID to filter by

    Returns:
        DataFrame with medicine-level aggregations
    """
    if clinic_id:
        df = df[df['clinic_id'] == clinic_id]

    summary = df.groupby(['medicine_name', 'medicine_category']).agg({
        'stockout': 'mean',
        'ending_stock': 'last',
        'consumption_rate': 'mean',
        'quantity_dispensed': 'mean'
    }).reset_index()

    summary.columns = [
        'medicine_name', 'category', 'stockout_rate',
        'current_stock', 'avg_consumption', 'avg_dispensed'
    ]

    summary['stockout_rate'] = (summary['stockout_rate'] * 100).round(1)

    return summary
