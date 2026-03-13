#!/usr/bin/env python
"""
Standalone script for retraining the stockout prediction model.

Usage:
    python scripts/retrain_model.py

Can be scheduled via:
    - Windows Task Scheduler (monthly)
    - Linux cron: 0 2 1 * * cd /path/to/project && ./venv/bin/python scripts/retrain_model.py
"""
import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import joblib
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, roc_auc_score

import config

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def retrain_model() -> dict:
    """
    Retrain the stockout prediction model with all available data.

    Returns:
        Dictionary with training metrics
    """
    logger.info("Starting model retraining...")

    # Load data
    df = pd.read_csv(config.DATA_PATH)
    logger.info(f"Loaded {len(df)} records")

    # Encode categories
    le = LabelEncoder()
    df['medicine_category_encoded'] = le.fit_transform(df['medicine_category'])

    # Time-based split (train on all but last 12 months)
    latest = df['month'].max()
    cutoff = (pd.to_datetime(latest) - pd.DateOffset(months=12)).strftime('%Y-%m')

    train_df = df[df['month'] < cutoff]
    test_df = df[df['month'] >= cutoff]

    X_train = train_df[config.FEATURES]
    y_train = train_df['stockout']
    X_test = test_df[config.FEATURES]
    y_test = test_df['stockout']

    logger.info(f"Training: {len(X_train)} samples, Testing: {len(X_test)} samples")

    # Train model
    model = GradientBoostingClassifier(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=5,
        min_samples_split=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_prob)

    logger.info(f"Accuracy: {accuracy:.4f}, AUC: {auc:.4f}")

    # Create models directory if needed
    config.MODELS_DIR.mkdir(exist_ok=True)

    # Save artifacts
    joblib.dump(model, config.MODEL_PATH)
    joblib.dump(le, config.ENCODER_PATH)
    joblib.dump(config.FEATURES, config.FEATURES_PATH)

    # Save metadata
    metadata = {
        'model_type': 'GradientBoostingClassifier',
        'trained_at': datetime.now().isoformat(),
        'training_samples': len(X_train),
        'test_samples': len(X_test),
        'training_period': f"{train_df['month'].min()} to {train_df['month'].max()}",
        'test_accuracy': accuracy,
        'test_auc': auc,
        'features': config.FEATURES,
        'categories': list(le.classes_)
    }
    joblib.dump(metadata, config.METADATA_PATH)

    logger.info("Model saved successfully!")

    return {
        'accuracy': accuracy,
        'auc': auc,
        'training_samples': len(X_train),
        'test_samples': len(X_test)
    }


def main():
    """Main entry point."""
    try:
        result = retrain_model()
        print("\n" + "=" * 50)
        print("Model Retraining Complete")
        print("=" * 50)
        print(f"Accuracy: {result['accuracy']:.1%}")
        print(f"AUC: {result['auc']:.3f}")
        print(f"Training samples: {result['training_samples']:,}")
        print(f"Test samples: {result['test_samples']:,}")
        print("=" * 50)
        return 0
    except Exception as e:
        logger.error(f"Retraining failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
