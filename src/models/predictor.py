"""
Model loading and prediction functions.
"""
import os
import pandas as pd
import numpy as np
import joblib
import streamlit as st
import config
from src.utils.risk import get_risk_level, calculate_days_until_stockout
from src.utils.reorder import calculate_reorder


@st.cache_resource
def load_model():
    """
    Load pre-trained model from disk.

    Returns:
        Tuple of (model, label_encoder, features_list)
    """
    if not os.path.exists(config.MODEL_PATH):
        st.error("Model not found. Please run the training notebook first.")
        st.stop()

    model = joblib.load(config.MODEL_PATH)
    le = joblib.load(config.ENCODER_PATH)
    features = joblib.load(config.FEATURES_PATH)

    return model, le, features


@st.cache_data
def load_model_metadata() -> dict:
    """
    Load model metadata.

    Returns:
        Dictionary with model info or None if not found
    """
    if os.path.exists(config.METADATA_PATH):
        return joblib.load(config.METADATA_PATH)
    return None


def predict_stockout(
    model,
    le,
    features: list,
    input_data: dict
) -> dict:
    """
    Make stockout prediction for given input.

    Args:
        model: Trained model
        le: Label encoder for categories
        features: Feature list
        input_data: Dictionary with input values

    Returns:
        Dictionary with prediction results
    """
    # Encode category
    category_encoded = le.transform([input_data['medicine_category']])[0]

    # Build feature vector
    X = pd.DataFrame({
        'remoteness_score': [input_data['remoteness_score']],
        'population_served': [input_data['population_served']],
        'medicine_category_encoded': [category_encoded],
        'month_num': [input_data['month_num']],
        'is_rainy_season': [input_data['is_rainy_season']],
        'beginning_stock': [input_data['beginning_stock']],
        'quantity_received': [input_data['quantity_received']],
        'quantity_dispensed': [input_data['quantity_dispensed']],
        'patient_visits': [input_data['patient_visits']],
        'days_since_last_delivery': [input_data['days_since_last_delivery']],
        'consumption_rate': [input_data['consumption_rate']],
        'stock_to_consumption_ratio': [input_data['stock_to_consumption_ratio']],
        'rolling_avg_consumption': [input_data['rolling_avg_consumption']],
        'prev_month_stockout': [input_data.get('prev_month_stockout', 0)]
    })

    # Get prediction
    probability = model.predict_proba(X)[0][1]
    risk_level, risk_color = get_risk_level(probability)

    # Calculate days until stockout
    ending_stock = max(0, input_data['beginning_stock'] +
                       input_data['quantity_received'] -
                       input_data['quantity_dispensed'])
    days_until_stockout = calculate_days_until_stockout(
        ending_stock, input_data['consumption_rate']
    )

    # Get reorder recommendation
    reorder = calculate_reorder(
        ending_stock=ending_stock,
        consumption_rate=input_data['consumption_rate'],
        rolling_avg_consumption=input_data['rolling_avg_consumption'],
        remoteness_score=input_data['remoteness_score'],
        is_rainy_season=bool(input_data['is_rainy_season'])
    )

    return {
        'probability': probability,
        'risk_level': risk_level,
        'risk_color': risk_color,
        'days_until_stockout': days_until_stockout,
        'ending_stock': ending_stock,
        'reorder': reorder
    }


def predict_batch(model, le, features: list, df: pd.DataFrame) -> pd.DataFrame:
    """
    Make predictions for a batch of records.

    Args:
        model: Trained model
        le: Label encoder
        features: Feature list
        df: DataFrame with input data

    Returns:
        DataFrame with predictions added
    """
    df_pred = df.copy()

    # Encode categories
    df_pred['medicine_category_encoded'] = le.transform(df_pred['medicine_category'])

    # Get predictions
    X = df_pred[features]
    probabilities = model.predict_proba(X)[:, 1]

    # Add prediction columns
    df_pred['stockout_probability'] = probabilities
    df_pred['risk_level'] = df_pred['stockout_probability'].apply(
        lambda x: get_risk_level(x)[0]
    )
    df_pred['risk_color'] = df_pred['stockout_probability'].apply(
        lambda x: get_risk_level(x)[1]
    )

    # Calculate days until stockout
    df_pred['days_until_stockout'] = df_pred.apply(
        lambda row: calculate_days_until_stockout(
            row['ending_stock'], row['consumption_rate']
        ), axis=1
    )

    # Calculate reorder urgency
    df_pred['reorder_urgency'] = df_pred.apply(
        lambda row: calculate_reorder(
            row['ending_stock'],
            row['consumption_rate'],
            row['rolling_avg_consumption'],
            row['remoteness_score'],
            bool(row['is_rainy_season'])
        ).urgency, axis=1
    )

    df_pred['reorder_action'] = df_pred.apply(
        lambda row: calculate_reorder(
            row['ending_stock'],
            row['consumption_rate'],
            row['rolling_avg_consumption'],
            row['remoteness_score'],
            bool(row['is_rainy_season'])
        ).action, axis=1
    )

    return df_pred
