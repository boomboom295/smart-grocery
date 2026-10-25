"""Command-line meal planner.

    python main.py --budget 20 --strategy knapsack_max_recipes
    python main.py --compare        # run every strategy and write data/compare.md
"""
import argparse
import json

from smart_grocery.experiments import run_suite
from smart_grocery.io import load_pantry
from smart_grocery.planner import STRATEGIES, plan
from smart_grocery.report import to_markdown, write_csvs


def parse_args():
    p = argparse.ArgumentParser(description="Plan a week of meals under a grocery budget.")
    p.add_argument("--recipes", default="data/recipes.json")
    p.add_argument("--pantry", default="data/pantry.sample.json")
    p.add_argument("--budget", type=float, default=20.0, help="grocery budget in dollars")
    p.add_argument("--max_time", type=int, default=30, help="max cooking time per recipe (minutes)")
    p.add_argument("--k_new", type=int, default=2, help="k for RMR@k: recipes needing at most k new items")
    p.add_argument("--strategy", choices=STRATEGIES, default="knapsack_max_recipes")
    p.add_argument("--price_overrides", default=None, help="JSON file of {ingredient: price}")
    p.add_argument("--max_calories_per_meal", type=int, default=None)
    p.add_argument("--out", default="data/plan.output.json")
    p.add_argument("--report_md", default="data/plan.report.md")
    p.add_argument("--grocery_csv", default="data/grocery_list.csv")
    p.add_argument("--recipes_csv", default="data/chosen_recipes.csv")
    p.add_argument("--no_report", action="store_true", help="skip the markdown/CSV reports")
    p.add_argument("--compare", action="store_true", help="compare all strategies")
    return p.parse_args()


def main():
    args = parse_args()
    if args.compare:
        rows = run_suite(args.recipes, args.pantry, budget=args.budget, max_time=args.max_time, k_new=args.k_new)
        for r in rows:
            print(f"{r['strategy']:<22} recipes={r['n_recipes']:<3} spend=${r['spend']:.2f}  RMR@k(chosen)={r['rmr_chosen']}%")
        print("wrote data/compare.md")
        return

    res = plan(
        recipes_path=args.recipes,
        pantry_items=load_pantry(args.pantry),
        budget=args.budget,
        max_time=args.max_time,
        k_new=args.k_new,
        strategy=args.strategy,
        price_overrides_path=args.price_overrides,
        max_calories_per_meal=args.max_calories_per_meal,
    )
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    if not args.no_report:
        with open(args.report_md, "w") as f:
            f.write(to_markdown(res))
        write_csvs(res, args.grocery_csv, args.recipes_csv)

    m = res["metrics"]
    print(f"{len(res['recipes'])} recipes, spend ${m['total_spend']:.2f} of ${m['target_budget']:.2f}")
    for r in res["recipes"]:
        print(f"  - {r['name']} ({r['time_min']} min, ${r['est_total_cost']:.2f})")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
