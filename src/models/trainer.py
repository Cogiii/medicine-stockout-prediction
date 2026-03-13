"""
Dashboard training integration.
"""
import sys
from pathlib import Path

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))


def retrain_model() -> dict:
    """
    Retrain the model (wrapper for dashboard use).

    Returns:
        Dictionary with training metrics
    """
    from retrain_model import retrain_model as _retrain
    return _retrain()
