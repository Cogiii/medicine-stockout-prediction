"""
Material Symbols icon mappings for consistent UI.
Format: ":material/icon_name:" (snake_case)
Reference: https://fonts.google.com/icons?icon.set=Material+Symbols
"""

ICONS = {
    # Risk indicators
    "risk_high": ":material/error:",
    "risk_medium": ":material/warning:",
    "risk_low": ":material/check_circle:",

    # Navigation
    "dashboard": ":material/dashboard:",
    "inventory": ":material/inventory_2:",
    "analytics": ":material/bar_chart:",
    "predict": ":material/psychology:",

    # Entities
    "medicine": ":material/medication:",
    "clinic": ":material/local_hospital:",
    "category": ":material/category:",

    # Actions
    "alert": ":material/notification_important:",
    "refresh": ":material/refresh:",
    "download": ":material/download:",
    "filter": ":material/filter_list:",
    "search": ":material/search:",
    "train": ":material/model_training:",
    "settings": ":material/settings:",

    # Status
    "info": ":material/info:",
    "summary": ":material/summarize:",
    "trend_up": ":material/trending_up:",
    "trend_down": ":material/trending_down:",

    # Time/Season
    "rainy": ":material/water_drop:",
    "dry": ":material/wb_sunny:",
    "calendar": ":material/calendar_month:",

    # Stock
    "stock_low": ":material/production_quantity_limits:",
    "stock_ok": ":material/inventory:",
    "delivery": ":material/local_shipping:",

    # Simulation & Comparison
    "simulation": ":material/show_chart:",
    "compare": ":material/compare_arrows:",
    "add": ":material/add_circle:",
    "load": ":material/cloud_download:",
    "timeline": ":material/timeline:",
    "scenario": ":material/science:",
    "clear": ":material/delete_sweep:",
    "save": ":material/save:",
}


def get_icon(name: str) -> str:
    """
    Get Material Symbol icon by semantic name.

    Args:
        name: Icon key from ICONS dictionary

    Returns:
        Material Symbol string or help icon if not found
    """
    return ICONS.get(name, ":material/help:")
