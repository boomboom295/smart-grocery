# smart_grocery/filtering.py
from __future__ import annotations
from typing import Dict, List, Set
from .models import Recipe, RecipeCostView, PricedIngredient
from .normalize import norm

# ---------- Price map ----------

def build_price_map(overrides: Dict[str, float] | None) -> Dict[str, float]:
    base_prices = {
        "onion": 0.5, "garlic": 0.4, "olive oil": 0.3, "oil": 0.3,
        "pepper": 0.2, "salt": 0.1, "pasta": 1.2, "rice": 1.0,
        "tomato": 1.0, "basil": 0.8, "parmesan": 3.2, "butter": 1.0,
        "carrot": 0.6, "broccoli": 1.2, "chickpea": 1.0, "lemon": 0.5,
        "bread": 1.8, "avocado": 1.5, "vegetable broth": 1.2,
        "tofu": 2.2, "turmeric": 1.0,
    }
    price_map = {norm(k): float(v) for k, v in base_prices.items()}
    for k, v in (overrides or {}).items():
        price_map[norm(k)] = float(v)
    return price_map

# ---------- Cost view ----------

def compute_cost_view(recipes: List[Recipe], pantry_items: List[str], price_map: Dict[str, float]) -> List[RecipeCostView]:
    pset: Set[str] = {norm(x) for x in (pantry_items or [])}
    out: List[RecipeCostView] = []

    for r in recipes:
        existing_names: Set[str] = set()
        missing_priced: List[PricedIngredient] = []
        est_total = 0.0

        for ing in r.ingredients:
            key = norm(ing.name)
            if key in pset:
                existing_names.add(ing.name)  # keep original display spelling
            else:
                price = float(price_map.get(key, 1.0))
                missing_priced.append(PricedIngredient(name=ing.name, price=price))
                est_total += price

        out.append(RecipeCostView(
            recipe=r,
            existing=sorted(existing_names),
            missing=missing_priced,
            est_total_cost=round(est_total, 2),
        ))
    return out

# ---------- Filters ----------

def filter_by_time(cvs: List[RecipeCostView], max_time: int) -> List[RecipeCostView]:
    if not max_time or max_time <= 0:
        return cvs
    return [cv for cv in cvs if (cv.recipe.time_min or 0) <= max_time]

def filter_by_calories(cvs: List[RecipeCostView], max_calories: int) -> List[RecipeCostView]:
    if not max_calories or max_calories <= 0:
        return cvs
    return [cv for cv in cvs if (cv.recipe.calories or 0) <= max_calories]

# ---------- Ranking ----------

def rank_by_cost_then_time(cvs: List[RecipeCostView]) -> List[RecipeCostView]:
    return sorted(
        cvs,
        key=lambda cv: (cv.est_total_cost, cv.recipe.time_min or 0, len(cv.missing))
    )

def rank_pantry_first(cvs: List[RecipeCostView]) -> List[RecipeCostView]:
    return sorted(
        cvs,
        key=lambda cv: (len(cv.missing), cv.est_total_cost, cv.recipe.time_min or 0)
    )
