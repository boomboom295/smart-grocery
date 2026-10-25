from typing import Dict

SNIPPET1 = """import re

UNITS = ["tablespoon","tablespoons","teaspoon","teaspoons","kilogram","kilograms","milliliter","milliliters","liter","liters","pound","pounds","ounce","ounces","grams","gram","cup","cups","tsp","tbsp","oz","g","kg","ml","l","lb"]
UNIT_RE = re.compile(r"\\b(" + "|".join(map(re.escape, UNITS)) + r")\\b")

def normalize_ingredient(text: str) -> str:
    x = text.strip().lower()
    x = re.sub(r"\\d+(\\.\\d+)?\\s*x?", " ", x)
    x = UNIT_RE.sub(" ", x)
    x = re.sub(r"[^a-z\\s]", " ", x)
    x = re.sub(r"\\s+", " ", x)
    return x.strip()"""

SNIPPET2 = """def greedy_cost(ranked, budget):
    chosen = []
    spend = 0.0
    for cv in ranked:
        if spend + cv.est_total_cost <= budget:
            chosen.append(cv)
            spend += cv.est_total_cost
    return chosen, round(spend, 2)"""

def write_checkpoint_qmd(res: Dict, path: str) -> None:
    lines = []
    lines.append('---')
    lines.append('title: "Project Checkpoint 1: Preliminary Code & Results"')
    lines.append('format: revealjs')
    lines.append('---')
    lines.append('')
    lines.append('## Problem Statement & Goal')
    lines.append('')
    lines.append('Meal planning that meets calorie, cost, and time goals is tedious and wasteful.')
    lines.append('Goal: Recommend meals and auto-generate a grocery list under budget, time, and pantry constraints.')
    lines.append('')
    lines.append('## Methodology Overview')
    lines.append('')
    lines.append('Text-based retrieval over structured recipes, normalization, budget/time filtering, selection strategy, and list aggregation.')
    lines.append('')
    lines.append('## Code Snippet 1')
    lines.append('')
    lines.append('```python')
    lines.append(SNIPPET1)
    lines.append('```')
    lines.append('')
    lines.append('## Explanation: Snippet 1')
    lines.append('')
    lines.append('Standardizes ingredient text for pantry matching and pricing to reduce mismatches and duplication.')
    lines.append('')
    lines.append('## Code Snippet 2')
    lines.append('')
    lines.append('```python')
    lines.append(SNIPPET2)
    lines.append('```')
    lines.append('')
    lines.append('## Explanation: Snippet 2')
    lines.append('')
    lines.append('Greedy selection adds recipes while staying under budget, forming a minimal viable planner.')
    lines.append('')
    lines.append('## Preliminary Result')
    lines.append('')
    lines.append('### Metrics')
    m = res["metrics"]
    lines.append(f'- Strategy: {m["strategy"]}')
    lines.append(f'- Target budget: ${m["target_budget"]}')
    lines.append(f'- Total spend: ${m["total_spend"]}')
    lines.append(f'- Budget adherence %: {m["budget_adherence_percent"]}')
    lines.append(f'- RMR% (all): {m["rmr_percent_at_k_all"]}')
    lines.append(f'- RMR% (chosen): {m["rmr_percent_at_k_chosen"]}')
    lines.append('')
    lines.append('### Chosen Recipes')
    for r in res["recipes"]:
        lines.append(f'- {r["name"]} | time {r["time_min"]} min | cal {r["calories"]} | cost ${r["est_total_cost"]}')
    lines.append('')
    lines.append('## Result Analysis & Next Steps')
    lines.append('')
    lines.append('Early pipeline works end-to-end; next add nutrition API, store price API, and multi-objective selection.')
    with open(path, "w") as f:
        f.write("\n".join(lines))
