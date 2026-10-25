"""Ways to choose recipes so the shopping cost stays within budget."""
from typing import List, Tuple
from .models import RecipeCostView

def greedy_cost(ranked: List[RecipeCostView], budget: float) -> Tuple[List[RecipeCostView], float]:
    chosen = []
    spend = 0.0
    for cv in ranked:
        if spend + cv.est_total_cost <= budget:
            chosen.append(cv)
            spend += cv.est_total_cost
    return chosen, round(spend, 2)

def greedy_low_missing(ranked: List[RecipeCostView], budget: float) -> Tuple[List[RecipeCostView], float]:
    s = sorted(ranked, key=lambda x: (len(x.missing), x.est_total_cost, x.recipe.time_min or 0))
    return greedy_cost(s, budget)

def knapsack_max_recipes(ranked: List[RecipeCostView], budget: float) -> Tuple[List[RecipeCostView], float]:
    """0/1 knapsack (costs in cents): pick the largest number of recipes that fit the budget.

    Among plans with the same number of recipes it prefers the one needing the fewest new
    ingredients, so it uses more of the pantry than plain greedy-by-cost.
    """
    n = len(ranked)
    W = int(round(budget * 100))
    wt = [int(round(cv.est_total_cost * 100)) for cv in ranked]
    big = 1000  # one more recipe always beats any saving in missing items
    val = [big - len(cv.missing) for cv in ranked]
    dp = [[0] * (W + 1) for _ in range(n + 1)]
    keep = [[0] * (W + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        wi = wt[i - 1]
        vi = val[i - 1]
        for w in range(W + 1):
            a = dp[i - 1][w]
            b = -1
            if wi <= w:
                t = vi + dp[i - 1][w - wi]
                if t > a:
                    b = t
            if b >= a:
                dp[i][w] = b
                if b != -1:
                    keep[i][w] = 1
            else:
                dp[i][w] = a
    w = W
    idx = []
    for i in range(n, 0, -1):
        if keep[i][w] == 1:
            idx.append(i - 1)
            w -= wt[i - 1]
    idx.reverse()
    chosen = [ranked[i] for i in idx]
    spend = round(sum(cv.est_total_cost for cv in chosen), 2)
    return chosen, spend

def select(ranked: List[RecipeCostView], budget: float, strategy: str) -> Tuple[List[RecipeCostView], float]:
    if strategy == "greedy_low_missing":
        return greedy_low_missing(ranked, budget)
    if strategy == "knapsack_max_recipes":
        return knapsack_max_recipes(ranked, budget)
    return greedy_cost(ranked, budget)
