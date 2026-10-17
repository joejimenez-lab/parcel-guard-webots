"""JSON-safe status encoding for the browser and test observers."""
import json
import math


def encode_status(value):
    def clean(item):
        if isinstance(item, float) and not math.isfinite(item):
            return None
        if isinstance(item, dict):
            return {key: clean(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [clean(child) for child in item]
        return item

    return json.dumps(clean(value), allow_nan=False)
