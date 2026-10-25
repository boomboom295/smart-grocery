from typing import List
from .models import RecipeCostView

def rmr(cost_views: List[RecipeCostView], k: int) -> float:
    if not cost_views:
        return 0.0
    ok = sum(1 for cv in cost_views if len(cv.missing) <= k)
    return round(100.0 * ok / len(cost_views), 2)

def budget_adherence(actual_spend: float, target_budget: float) -> float:
    if target_budget <= 0:
        return 0.0
    return round(abs(actual_spend - target_budget) / target_budget * 100.0, 2)
