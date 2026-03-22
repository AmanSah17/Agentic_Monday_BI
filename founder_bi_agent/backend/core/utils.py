import math
from datetime import date, datetime
from typing import Any
import numpy as np
import pandas as pd

def sanitize_for_json(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        return None if math.isnan(value) or math.isinf(value) else value

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if value is pd.NaT:
        return None

    if isinstance(value, pd.Timestamp):
        return None if pd.isna(value) else value.isoformat()

    # Pandas nullable types/numpy types can be tricky
    if hasattr(value, "item") and callable(getattr(value, "item")):
        return sanitize_for_json(value.item())

    if isinstance(value, dict):
        return {str(k): sanitize_for_json(v) for k, v in value.items()}

    if isinstance(value, (list, tuple, set)):
        return [sanitize_for_json(v) for v in value]

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    # Final attempt to ensure numeric safety for Recharts
    if isinstance(value, (float, np.floating)):
        if math.isnan(value) or math.isinf(value):
            return 0.0 # Force 0 for charts
        return float(value)
    
    if isinstance(value, (int, np.integer)):
        return int(value)

    return str(value)
