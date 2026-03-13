"""
Generate synthetic medicine inventory data for rural health clinics in Mindanao.

Creates a dataset with:
- 10 clinics (Mindanao RHUs)
- 15 essential medicines
- 63 months of records (Jan 2021 – Mar 2026)
- ~9,450 total rows
- ~22% stockout rate

Usage: python scripts/generate_data.py
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

np.random.seed(42)

# Output path
OUTPUT_DIR = Path(__file__).parent.parent / "data"
OUTPUT_DIR.mkdir(exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "medicine_inventory_data.csv"

# Define clinics with their characteristics
clinics = [
    {"clinic_id": 1, "clinic_name": "Davao City RHU", "remoteness_score": 0.1, "population_served": 50000},
    {"clinic_id": 2, "clinic_name": "General Santos RHU", "remoteness_score": 0.15, "population_served": 45000},
    {"clinic_id": 3, "clinic_name": "Cotabato City RHU", "remoteness_score": 0.25, "population_served": 35000},
    {"clinic_id": 4, "clinic_name": "Zamboanga RHU", "remoteness_score": 0.3, "population_served": 40000},
    {"clinic_id": 5, "clinic_name": "Butuan City RHU", "remoteness_score": 0.35, "population_served": 30000},
    {"clinic_id": 6, "clinic_name": "Maguindanao RHU", "remoteness_score": 0.6, "population_served": 20000},
    {"clinic_id": 7, "clinic_name": "Lanao del Sur RHU", "remoteness_score": 0.7, "population_served": 18000},
    {"clinic_id": 8, "clinic_name": "Sarangani RHU", "remoteness_score": 0.75, "population_served": 15000},
    {"clinic_id": 9, "clinic_name": "Tawi-Tawi RHU", "remoteness_score": 0.85, "population_served": 12000},
    {"clinic_id": 10, "clinic_name": "Sulu RHU", "remoteness_score": 0.9, "population_served": 10000},
]

# Define medicines with their categories
medicines = [
    {"medicine_name": "Amoxicillin 500mg", "medicine_category": "Antibiotic"},
    {"medicine_name": "Co-Amoxiclav 625mg", "medicine_category": "Antibiotic"},
    {"medicine_name": "Metronidazole 500mg", "medicine_category": "Antibiotic"},
    {"medicine_name": "Oral Rehydration Salts", "medicine_category": "ORS"},
    {"medicine_name": "Zinc Sulfate 20mg", "medicine_category": "ORS"},
    {"medicine_name": "Paracetamol 500mg", "medicine_category": "Analgesic"},
    {"medicine_name": "Ibuprofen 400mg", "medicine_category": "Analgesic"},
    {"medicine_name": "Mefenamic Acid 500mg", "medicine_category": "Analgesic"},
    {"medicine_name": "Losartan 50mg", "medicine_category": "Chronic"},
    {"medicine_name": "Amlodipine 5mg", "medicine_category": "Chronic"},
    {"medicine_name": "Metformin 500mg", "medicine_category": "Chronic"},
    {"medicine_name": "Salbutamol 2mg", "medicine_category": "Respiratory"},
    {"medicine_name": "Cetirizine 10mg", "medicine_category": "Respiratory"},
    {"medicine_name": "Ferrous Sulfate 325mg", "medicine_category": "Vitamin"},
    {"medicine_name": "Ascorbic Acid 500mg", "medicine_category": "Vitamin"},
]

# Generate 63 months of dates (Jan 2021 - Mar 2026)
months = pd.date_range(start='2021-01-01', end='2026-03-01', freq='MS')

def is_rainy_season(month):
    """June to November is rainy season in Mindanao"""
    return month.month >= 6 and month.month <= 11

def generate_record(clinic, medicine, month, prev_stockout=0, prev_consumption=None):
    """Generate a single inventory record"""

    remoteness = clinic["remoteness_score"]
    population = clinic["population_served"]
    category = medicine["medicine_category"]
    rainy = is_rainy_season(month)

    # Base consumption depends on population and medicine type
    base_consumption = population / 1000  # Rough scaling

    # Category-specific adjustments
    category_multipliers = {
        "Antibiotic": 1.2,
        "ORS": 1.0,
        "Analgesic": 1.5,
        "Chronic": 0.8,
        "Respiratory": 0.9,
        "Vitamin": 0.7,
    }
    base_consumption *= category_multipliers.get(category, 1.0)

    # Rainy season increases demand for antibiotics and ORS
    if rainy and category in ["Antibiotic", "ORS"]:
        base_consumption *= 1.4
    elif rainy and category == "Respiratory":
        base_consumption *= 1.2

    # Add random variation
    consumption_variation = np.random.uniform(0.7, 1.3)
    quantity_dispensed = int(base_consumption * consumption_variation)

    # Patient visits correlate with consumption
    patient_visits = int(quantity_dispensed * np.random.uniform(0.8, 1.2))

    # Beginning stock - varies based on previous period and remoteness
    if prev_consumption is not None:
        # Expected stock based on previous consumption
        expected_stock = int(prev_consumption * 1.5)
    else:
        expected_stock = int(base_consumption * 2)

    # Remote clinics have more variable stock levels
    stock_variation = np.random.uniform(0.5, 1.5) if remoteness > 0.5 else np.random.uniform(0.7, 1.3)
    beginning_stock = max(0, int(expected_stock * stock_variation))

    # Quantity received - remote clinics get less reliable deliveries
    delivery_reliability = 1 - (remoteness * 0.6)  # 0.4 to 1.0 reliability

    # Sometimes deliveries are delayed or missed for remote areas
    if np.random.random() > delivery_reliability:
        quantity_received = 0
        days_since_last_delivery = np.random.randint(30, 90)
    else:
        # Normal delivery
        target_delivery = int(base_consumption * 2)
        quantity_received = int(target_delivery * np.random.uniform(0.8, 1.2))
        days_since_last_delivery = np.random.randint(7, 35)

    # Calculate ending stock
    ending_stock = max(0, beginning_stock + quantity_received - quantity_dispensed)

    # Determine stockout (ending stock is 0 or very low relative to consumption)
    consumption_rate = quantity_dispensed / max(1, 30)  # daily rate
    stock_to_consumption_ratio = ending_stock / max(1, quantity_dispensed)

    # Stockout if ending stock can't cover even a week of consumption
    stockout = 1 if ending_stock < (consumption_rate * 7) else 0

    # Additional stockout probability for remote clinics with supply issues
    if remoteness > 0.6 and np.random.random() < 0.15:
        stockout = 1

    # Rolling 3-month average (will be calculated later)
    rolling_avg_consumption = quantity_dispensed  # Placeholder

    return {
        "clinic_id": clinic["clinic_id"],
        "clinic_name": clinic["clinic_name"],
        "remoteness_score": remoteness,
        "population_served": population,
        "medicine_name": medicine["medicine_name"],
        "medicine_category": category,
        "month": month.strftime("%Y-%m"),
        "year": month.year,
        "month_num": month.month,
        "is_rainy_season": int(rainy),
        "beginning_stock": beginning_stock,
        "quantity_received": quantity_received,
        "quantity_dispensed": quantity_dispensed,
        "ending_stock": ending_stock,
        "patient_visits": patient_visits,
        "days_since_last_delivery": days_since_last_delivery,
        "consumption_rate": round(consumption_rate, 2),
        "stock_to_consumption_ratio": round(stock_to_consumption_ratio, 2),
        "rolling_avg_consumption": rolling_avg_consumption,
        "prev_month_stockout": prev_stockout,
        "stockout": stockout,
    }

# Generate all records
records = []
for clinic in clinics:
    for medicine in medicines:
        prev_stockout = 0
        prev_consumption = None
        consumption_history = []

        for month in months:
            record = generate_record(clinic, medicine, month, prev_stockout, prev_consumption)

            # Update history
            consumption_history.append(record["quantity_dispensed"])
            if len(consumption_history) >= 3:
                record["rolling_avg_consumption"] = round(np.mean(consumption_history[-3:]), 2)
            else:
                record["rolling_avg_consumption"] = round(np.mean(consumption_history), 2)

            records.append(record)

            # Update for next iteration
            prev_stockout = record["stockout"]
            prev_consumption = record["quantity_dispensed"]

# Create DataFrame
df = pd.DataFrame(records)

# Reorder columns
column_order = [
    "clinic_id", "clinic_name", "remoteness_score", "population_served",
    "medicine_name", "medicine_category", "month", "year", "month_num",
    "is_rainy_season", "beginning_stock", "quantity_received", "quantity_dispensed",
    "ending_stock", "patient_visits", "days_since_last_delivery",
    "consumption_rate", "stock_to_consumption_ratio", "rolling_avg_consumption",
    "prev_month_stockout", "stockout"
]
df = df[column_order]

# Save to CSV
df.to_csv(OUTPUT_PATH, index=False)

# Print summary
print(f"Dataset generated: {len(df)} records")
print(f"Clinics: {df['clinic_id'].nunique()}")
print(f"Medicines: {df['medicine_name'].nunique()}")
print(f"Months: {df['month'].nunique()}")
print(f"Stockout rate: {df['stockout'].mean()*100:.1f}%")
print(f"\nStockout by remoteness:")
print(df.groupby(df['remoteness_score'] > 0.5)['stockout'].mean().round(3))
print(f"\nStockout by season (rainy vs dry):")
print(df.groupby('is_rainy_season')['stockout'].mean().round(3))
print(f"\nFile saved: {OUTPUT_PATH}")
