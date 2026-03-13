"""
Reorder recommendation logic.
"""
from dataclasses import dataclass
from typing import Literal
import config


@dataclass
class ReorderRecommendation:
    """Reorder recommendation data."""
    urgency: Literal["IMMEDIATE", "SOON", "SCHEDULED", "OK"]
    action: str
    suggested_quantity: int
    reason: str


def calculate_reorder(
    ending_stock: float,
    consumption_rate: float,
    rolling_avg_consumption: float,
    remoteness_score: float = 0.5,
    is_rainy_season: bool = False
) -> ReorderRecommendation:
    """
    Calculate reorder recommendation based on current stock and consumption.

    Thresholds:
    - IMMEDIATE: < 7 days coverage
    - SOON: 7-14 days coverage
    - SCHEDULED: 14-30 days coverage
    - OK: > 30 days coverage

    Args:
        ending_stock: Current stock level
        consumption_rate: Daily consumption rate
        rolling_avg_consumption: 3-month average consumption
        remoteness_score: Clinic remoteness (0-1)
        is_rainy_season: Whether it's rainy season

    Returns:
        ReorderRecommendation with urgency, action, quantity, and reason
    """
    # Calculate days of coverage
    days_coverage = ending_stock / max(0.1, consumption_rate)

    # Target days increases with remoteness (longer lead times)
    target_days = 45 + int(remoteness_score * 30)  # 45-75 days

    # Seasonal adjustment for rainy season
    seasonal_factor = 1.3 if is_rainy_season else 1.0

    # Calculate suggested quantity
    suggested_qty = int(
        (target_days * rolling_avg_consumption * seasonal_factor) - ending_stock
    )
    suggested_qty = max(0, suggested_qty)

    if days_coverage < config.REORDER_IMMEDIATE:
        return ReorderRecommendation(
            urgency="IMMEDIATE",
            action="Order now",
            suggested_quantity=suggested_qty,
            reason=f"{int(days_coverage)} days left"
        )
    elif days_coverage < config.REORDER_SOON:
        return ReorderRecommendation(
            urgency="SOON",
            action="Order this week",
            suggested_quantity=suggested_qty,
            reason=f"{int(days_coverage)} days left"
        )
    elif days_coverage < config.REORDER_SCHEDULED:
        return ReorderRecommendation(
            urgency="SCHEDULED",
            action="Order in 2-3 weeks",
            suggested_quantity=suggested_qty,
            reason=f"{int(days_coverage)} days left"
        )
    else:
        return ReorderRecommendation(
            urgency="OK",
            action="No action needed",
            suggested_quantity=0,
            reason=f"{int(days_coverage)} days stock"
        )


def get_urgency_color(urgency: str) -> str:
    """Get color for urgency level."""
    colors = {
        "IMMEDIATE": "red",
        "SOON": "orange",
        "SCHEDULED": "blue",
        "OK": "green"
    }
    return colors.get(urgency, "gray")
