from typing import Dict, List, Optional, Tuple
from .io import load_recipes, load_price_overrides, load_pantry
from .models import RecipeCostView
from .filtering import (
    build_price_map,
    compute_cost_view,
    filter_by_time,
    filter_by_calories,
    rank_by_cost_then_time,
    rank_pantry_first,
)

def _knapsack_max_count(items: List[Tuple[float, int]]) -> List[int]:
    # items: [(cost, idx)] maximize count under budget
    return [i for _, i in sorted(items, key=lambda t: t[0])]

def _select(strategy: str, ranked: List[RecipeCostView], budget: float) -> Tuple[List[RecipeCostView], float]:
    if budget is None:
        budget = 10.0
    if strategy == "greedy_cost":
        chosen, spend = [], 0.0
        for cv in ranked:
            if spend + cv.est_total_cost <= budget:
                chosen.append(cv)
                spend += cv.est_total_cost
        return chosen, round(spend, 2)
    # default knapsack-ish: sorted by cost, pack while feasible
    chosen, spend = [], 0.0
    for cv in ranked:
        if spend + cv.est_total_cost <= budget:
            chosen.append(cv)
            spend += cv.est_total_cost
    return chosen, round(spend, 2)

def _rmr_percent(cvs: List[RecipeCostView], k: int) -> float:
    if not cvs:
        return 0.0
    ok = sum(1 for cv in cvs if len(cv.missing) <= k)
    return round(100.0 * ok / len(cvs), 2)

def plan(
    recipes_path: str,
    pantry_items: List[str],
    budget: float,
    max_time: int,
    k_new: int,
    strategy: str = "knapsack_max_recipes",
    price_overrides_path: Optional[str] = None,
    max_calories_per_meal: Optional[int] = None
) -> Dict:
    recipes = load_recipes(recipes_path)
    overrides = load_price_overrides(price_overrides_path) if price_overrides_path else {}
    price_map = build_price_map(overrides)

    cvs = compute_cost_view(recipes, pantry_items, price_map)

    # keep fast stuff
    cvs = filter_by_time(cvs, max_time)

    # only filter calories if caller provided a limit
    if max_calories_per_meal is not None and max_calories_per_meal > 0:
        cvs = filter_by_calories(cvs, max_calories_per_meal)

    # ----- RANKING -----
    if strategy == "pantry_first":
        ranked = rank_pantry_first(cvs)           # favors more pantry overlap, then cost, then time
    else:
        ranked = rank_by_cost_then_time(cvs)      # your current default

    # ----- SELECTION (greedy pack under budget) -----
    chosen, spend = _select(strategy, ranked, budget)

    # Build grocery list from missing items
    grocery = {}
    for cv in chosen:
        for m in cv.missing:
            grocery[m.name] = grocery.get(m.name, 0.0) + float(m.price)
    grocery_list = [{"name": k, "est_price": round(v, 2)} for k, v in sorted(grocery.items())]

    # Metrics
    rmr_all = _rmr_percent(cvs, k_new)
    rmr_chosen = _rmr_percent(chosen, k_new) if chosen else 0.0
    ba = round(100.0 * (abs(budget - spend) / budget), 1) if budget else 0.0

    def _emit(cv: RecipeCostView) -> Dict:
        return {
            "name": cv.recipe.name,
            "time_min": cv.recipe.time_min,
            "calories": cv.recipe.calories,
            "missing": [{"name": m.name, "price": m.price} for m in cv.missing],
            "existing": list(cv.existing),
            "est_total_cost": round(cv.est_total_cost, 2),
            "ingredients": [ing.name for ing in cv.recipe.ingredients],
            "instructions": cv.recipe.instructions,
        }

    week = [_emit(chosen[i]) if i < len(chosen) else None for i in range(7)]

    return {
        "recipes": [_emit(cv) for cv in chosen],
        "metrics": {
            "strategy": "pantry_first" if strategy == "pantry_first" else strategy,
            "target_budget": float(budget),
            "total_spend": float(spend),
            "budget_adherence_percent": ba,
            "rmr_percent_at_k_all": rmr_all,
            "rmr_percent_at_k_chosen": rmr_chosen
        },
        "grocery_list": grocery_list,
        "week_plan": week
    }
