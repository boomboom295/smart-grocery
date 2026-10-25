import json
from typing import Dict, Optional

DEFAULT_PRICE = 2.0

def build_price_map(overrides_path: Optional[str] = None) -> Dict[str, float]:
    base = {
        "milk": 3.5,
        "eggs": 2.9,
        "sugar": 1.7,
        "flour": 2.2,
        "chicken breast": 4.5,
        "lettuce": 1.8,
        "tomato": 0.9,
        "pasta": 1.6,
        "olive oil": 5.0,
        "garlic": 0.5,
        "onion": 0.8,
        "salt": 0.5,
        "pepper": 0.7,
        "parmesan": 3.2,
        "cucumber": 1.2,
        "carrot": 0.6
    }
    if overrides_path:
        try:
            with open(overrides_path, "r") as f:
                data = json.load(f)
            for k, v in data.items():
                base[str(k).strip().lower()] = float(v)
        except Exception:
            pass
    return base

def price_for(name: str, price_map: Dict[str, float]) -> float:
    return price_map.get(name, DEFAULT_PRICE)
