import itertools
from pathlib import Path

import pytest

from smart_grocery.models import Ingredient, PricedIngredient, Recipe, RecipeCostView
from smart_grocery.normalize import norm
from smart_grocery.planner import STRATEGIES, plan
from smart_grocery.selection import greedy_cost, knapsack_max_recipes

ROOT = Path(__file__).resolve().parents[1]
RECIPES = str(ROOT / "data" / "recipes.json")
PANTRY = ["eggs", "onion", "garlic", "rice", "pasta", "olive oil", "salt", "pepper", "butter"]


def cv(name, cost, n_missing=1):
    missing = [PricedIngredient(f"{name}-{i}", cost / n_missing) for i in range(n_missing)]
    return RecipeCostView(recipe=Recipe(name=name, ingredients=[Ingredient(name)]), missing=missing, est_total_cost=cost)


@pytest.mark.parametrize("raw, expected", [
    ("Onions", "onion"),
    ("chopped red onion", "onion"),
    ("Cooked Rice", "rice"),
    ("garlic cloves", "garlic"),
    ("spaghetti", "pasta"),
])
def test_norm_canonicalizes_ingredients(raw, expected):
    assert norm(raw) == expected


def test_knapsack_matches_brute_force():
    items = [cv("a", 4.5), cv("b", 3.2), cv("c", 2.9), cv("d", 6.1), cv("e", 1.4), cv("f", 5.0)]
    budget = 10.0
    best = max(
        len(combo)
        for r in range(len(items) + 1)
        for combo in itertools.combinations(items, r)
        if sum(x.est_total_cost for x in combo) <= budget + 1e-9
    )
    chosen, spend = knapsack_max_recipes(items, budget)
    assert len(chosen) == best
    assert spend <= budget


def test_knapsack_prefers_fewer_new_items_on_ties():
    # both pairs fit; the second pair needs fewer new ingredients
    items = [cv("a", 2.0, n_missing=3), cv("b", 2.0, n_missing=3), cv("c", 2.5, n_missing=1), cv("d", 2.5, n_missing=1)]
    chosen, _ = knapsack_max_recipes(items, 5.0)
    assert {x.recipe.name for x in chosen} == {"c", "d"}


def test_greedy_never_exceeds_budget():
    items = [cv("a", 4.0), cv("b", 4.0), cv("c", 4.0)]
    chosen, spend = greedy_cost(items, 9.0)
    assert len(chosen) == 2 and spend == 8.0


@pytest.mark.parametrize("strategy", STRATEGIES)
def test_plan_respects_constraints(strategy):
    res = plan(RECIPES, PANTRY, budget=15, max_time=20, k_new=2, strategy=strategy, max_calories_per_meal=500)
    assert res["recipes"], "expected at least one recipe"
    assert res["metrics"]["total_spend"] <= 15
    for r in res["recipes"]:
        assert r["time_min"] <= 20
        assert r["calories"] <= 500
        assert not set(map(norm, (m["name"] for m in r["missing"]))) & set(map(norm, PANTRY))


def test_grocery_list_covers_every_missing_item():
    res = plan(RECIPES, PANTRY, budget=20, max_time=30, k_new=2)
    missing = {m["name"] for r in res["recipes"] for m in r["missing"]}
    assert missing == {g["name"] for g in res["grocery_list"]}


def test_unknown_strategy_is_rejected():
    with pytest.raises(ValueError):
        plan(RECIPES, PANTRY, budget=10, max_time=30, k_new=2, strategy="nope")
