"""
Configuration constants for Medicine Stockout Prediction.
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_PATH = DATA_DIR / "medicine_inventory_data.csv"
MODELS_DIR = BASE_DIR / "models"
MODEL_PATH = MODELS_DIR / "stockout_model.pkl"
ENCODER_PATH = MODELS_DIR / "label_encoder.pkl"
FEATURES_PATH = MODELS_DIR / "model_features.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata.pkl"

# App settings
APP_NAME = "Medicine Stockout Prediction"
PAGE_ICON = ":material/medication:"

# Risk thresholds
RISK_HIGH_THRESHOLD = 0.7
RISK_MEDIUM_THRESHOLD = 0.4

# Reorder thresholds (days of coverage)
REORDER_IMMEDIATE = 7
REORDER_SOON = 14
REORDER_SCHEDULED = 30

# Model features
FEATURES = [
    'remoteness_score', 'population_served', 'medicine_category_encoded',
    'month_num', 'is_rainy_season', 'beginning_stock', 'quantity_received',
    'quantity_dispensed', 'patient_visits', 'days_since_last_delivery',
    'consumption_rate', 'stock_to_consumption_ratio', 'rolling_avg_consumption',
    'prev_month_stockout'
]

# Medicine categories
MEDICINE_CATEGORIES = [
    "Antibiotic", "ORS", "Analgesic", "Chronic", "Respiratory", "Vitamin"
]
