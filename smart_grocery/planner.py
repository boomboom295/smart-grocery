"""Turn a recipe catalog + pantry + constraints into a meal plan and shopping list."""
from __future__ import annotations

from typing import Dict, List, Optional

from .filtering import (
    build_price_map,
    compute_cost_view,
    filter_by_calories,
    filter_by_time,
    rank_by_cost_then_time,
)
from .io import load_catalog_prices, load_price_overrides, load_recipes
from .metrics import budget_adherence, rmr
from .models import RecipeCostView
from .selection import select

STRATEGIES = ("greedy_cost", "greedy_low_missing", "knapsack_max_recipes")


def _emit(cv: RecipeCostView) -> Dict:
    return {
        "name": cv.recipe.name,
        "time_min": cv.recipe.time_min,
        "calories": cv.recipe.calories,
        "missing": [{"name": m.name, "price": m.price} for m in cv.missing],
        "existing": list(cv.existing),
        "est_total_cost": round(cv.est_total_cost, 2),
        "ingredients": [ing.name for ing in cv.recipe.ingredients],
        "instructions": list(cv.recipe.instructions),
    }


def plan(
    recipes_path: str,
    pantry_items: List[str],
    budget: float,
    max_time: int,
    k_new: int,
    strategy: str = "knapsack_max_recipes",
    price_overrides_path: Optional[str] = None,
    max_calories_per_meal: Optional[int] = None,
) -> Dict:
    """Plan meals under a grocery budget.

    1. Price each recipe by the ingredients missing from the pantry.
    2. Drop recipes over the time / calorie limits.
    3. Rank, then pick recipes with the chosen strategy so spend stays within budget.
    """
    if strategy not in STRATEGIES:
        raise ValueError(f"unknown strategy {strategy!r}; choose one of {', '.join(STRATEGIES)}")

    recipes = load_recipes(recipes_path)
    prices = load_catalog_prices(recipes_path)
    prices.update(load_price_overrides(price_overrides_path))
    price_map = build_price_map(prices)

    cvs = compute_cost_view(recipes, pantry_items, price_map)
    cvs = filter_by_time(cvs, max_time)
    if max_calories_per_meal:
        cvs = filter_by_calories(cvs, max_calories_per_meal)

    chosen, spend = select(rank_by_cost_then_time(cvs), budget, strategy)

    grocery: Dict[str, float] = {}
    for cv in chosen:
        for m in cv.missing:
            grocery[m.name] = grocery.get(m.name, 0.0) + float(m.price)
    grocery_list = [{"name": k, "est_price": round(v, 2)} for k, v in sorted(grocery.items())]

    recipes_out = [_emit(cv) for cv in chosen]
    return {
        "recipes": recipes_out,
        "week_plan": recipes_out[:7],
        "grocery_list": grocery_list,
        "metrics": {
            "strategy": strategy,
            "max_calories_per_meal": max_calories_per_meal,
            "target_budget": float(budget),
            "total_spend": float(spend),
            # percent the spend deviates from the target budget (lower = closer to budget)
            "budget_adherence_percent": budget_adherence(spend, budget),
            "rmr_percent_at_k_all": rmr(cvs, k_new),
            "rmr_percent_at_k_chosen": rmr(chosen, k_new),
        },
    }
