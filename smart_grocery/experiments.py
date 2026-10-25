"""Run every selection strategy on the same inputs and compare them."""
import json
import os

from .io import load_pantry
from .planner import STRATEGIES, plan


def run_suite(recipes_path, pantry_path, budget=20.0, max_time=30, k_new=2, out_dir="data"):
    pantry = load_pantry(pantry_path)
    rows = []
    for strategy in STRATEGIES:
        m = plan(recipes_path, pantry, budget, max_time, k_new, strategy)
        rows.append({
            "strategy": strategy,
            "budget": m["metrics"]["target_budget"],
            "spend": m["metrics"]["total_spend"],
            "ba_pct": m["metrics"]["budget_adherence_percent"],
            "rmr_all": m["metrics"]["rmr_percent_at_k_all"],
            "rmr_chosen": m["metrics"]["rmr_percent_at_k_chosen"],
            "n_recipes": len(m["recipes"]),
        })

    md = [
        f"# Strategy comparison (budget ${budget:.0f}, max {max_time} min, k={k_new})",
        "",
        "| strategy | #recipes | spend | budget deviation % | RMR@k all % | RMR@k chosen % |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        md.append(f"| {r['strategy']} | {r['n_recipes']} | {r['spend']:.2f} | {r['ba_pct']:.1f} | {r['rmr_all']:.1f} | {r['rmr_chosen']:.1f} |")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "compare.md"), "w") as f:
        f.write("\n".join(md) + "\n")
    with open(os.path.join(out_dir, "compare.json"), "w") as f:
        json.dump(rows, f, indent=2)
    return rows
