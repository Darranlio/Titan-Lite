import math

def sanitize_json_data(obj):
    """
    Recursively replaces NaN values with None to ensure JSON compliance.
    Handles lists and dictionaries.
    """
    if isinstance(obj, list):
        return [sanitize_json_data(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: sanitize_json_data(v) for k, v in obj.items()}
    elif isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj
