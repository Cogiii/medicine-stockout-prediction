"""
Risk calculation utilities.
"""
from typing import Tuple
import config


def get_risk_level(probability: float) -> Tuple[str, str]:
    """
    Convert stockout probability to risk level.

    Args:
        probability: Stockout probability (0-1)

    Returns:
        Tuple of (level_name, color)
    """
    if probability >= config.RISK_HIGH_THRESHOLD:
        return "HIGH", "red"
    elif probability >= config.RISK_MEDIUM_THRESHOLD:
        return "MEDIUM", "orange"
    else:
        return "LOW", "green"


def calculate_days_until_stockout(
    ending_stock: float,
    consumption_rate: float
) -> int:
    """
    Calculate estimated days until stockout.

    Args:
        ending_stock: Current stock level (units)
        consumption_rate: Daily consumption rate (units/day)

    Returns:
        Days until stockout (999 if no consumption)
    """
    if consumption_rate <= 0:
        return 999  # No consumption = indefinite stock

    return max(0, int(ending_stock / consumption_rate))


def get_risk_badge(level: str) -> str:
    """
    Get risk level display with appropriate styling.

    Args:
        level: Risk level (HIGH, MEDIUM, LOW)

    Returns:
        Formatted badge string
    """
    badges = {
        "HIGH": "HIGH",
        "MEDIUM": "MEDIUM",
        "LOW": "LOW"
    }
    return badges.get(level, level)
