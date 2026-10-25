import json, os
from .planner import plan

def run_case(recipes, pantry, budget, max_time, k_new, strategy, price_overrides=None, max_cals=None):
    r = plan(
        recipes_path=recipes,
        pantry_path=pantry,
        budget=budget,
        max_time=max_time,
        k_new_items=k_new,
        strategy=strategy,
        price_overrides=price_overrides,
        max_calories_per_meal=max_cals
    )
    m = r["metrics"]
    return {
        "strategy": m["strategy"],
        "max_cal": m.get("max_calories_per_meal"),
        "budget": m["target_budget"],
        "spend": m["total_spend"],
        "ba_pct": m["budget_adherence_percent"],
        "rmr_all": m["rmr_percent_at_k_all"],
        "rmr_chosen": m["rmr_percent_at_k_chosen"],
        "n_recipes": len(r["recipes"])
    }, r

def run_suite(out_dir="data"):
    os.makedirs(out_dir, exist_ok=True)
    recipes = f"{out_dir}/recipes.sample.json"
    pantry = f"{out_dir}/pantry.sample.json"
    cases = [
        {"strategy":"greedy_cost","maxc":None,"ovr":None},
        {"strategy":"greedy_low_missing","maxc":None,"ovr":None},
        {"strategy":"knapsack_max_recipes","maxc":None,"ovr":None},
        {"strategy":"knapsack_max_recipes","maxc":600,"ovr":None},
        {"strategy":"greedy_low_missing","maxc":600,"ovr":f"{out_dir}/prices.override.json"}
    ]
    rows = []
    for c in cases:
        row, _ = run_case(recipes, pantry, 10.0, 30, 2, c["strategy"], c["ovr"], c["maxc"])
        rows.append(row)
    md = []
    md.append("# CP2 Comparison")
    md.append("")
    md.append("| strategy | max_cal | budget | spend | BA% | RMR% (all) | RMR% (chosen) | #recipes |")
    md.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        md.append(f"| {r['strategy']} | {r['max_cal'] if r['max_cal'] else '-'} | {r['budget']:.1f} | {r['spend']:.1f} | {r['ba_pct']:.1f} | {r['rmr_all']:.2f} | {r['rmr_chosen']:.2f} | {r['n_recipes']} |")
    with open(f"{out_dir}/cp2.compare.md","w") as f:
        f.write("\n".join(md))
    with open(f"{out_dir}/cp2.compare.json","w") as f:
        json.dump(rows, f, indent=2)
    return rows
