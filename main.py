import json
from smart_grocery.planner import plan
from smart_grocery.report import write_markdown, write_csvs
from smart_grocery.qmd import write_checkpoint_qmd
from smart_grocery.experiments import run_suite

def parse_args():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--recipes", default="data/recipes.sample.json")
    p.add_argument("--pantry", default="data/pantry.sample.json")
    p.add_argument("--budget", type=float, default=20.0)
    p.add_argument("--max_time", type=int, default=30)
    p.add_argument("--k_new", type=int, default=2)
    p.add_argument("--strategy", choices=["greedy_cost","greedy_low_missing","knapsack_max_recipes"], default="greedy_cost")
    p.add_argument("--price_overrides", default=None)
    p.add_argument("--max_calories_per_meal", type=int, default=None)
    p.add_argument("--out", default="data/plan.output.json")
    p.add_argument("--report_md", default="data/plan.report.md")
    p.add_argument("--grocery_csv", default="data/grocery_list.csv")
    p.add_argument("--recipes_csv", default="data/chosen_recipes.csv")
    p.add_argument("--qmd", default="data/checkpoint1.qmd")
    p.add_argument("--no_report", action="store_true")
    p.add_argument("--no_qmd", action="store_true")
    p.add_argument("--run_cp2_suite", action="store_true")
    return p.parse_args()

def main():
    args = parse_args()
    if args.run_cp2_suite:
        run_suite("data")
        print("data/cp2.compare.md")
        return
    res = plan(
        args.recipes,
        args.pantry,
        args.budget,
        args.max_time,
        args.k_new,
        args.strategy,
        args.price_overrides,
        args.max_calories_per_meal
    )
    with open(args.out, "w") as f:
        json.dump(res, f, indent=2)
    if not args.no_report:
        write_markdown(res, args.report_md)
        write_csvs(res, args.grocery_csv, args.recipes_csv)
    if not args.no_qmd:
        write_checkpoint_qmd(res, args.qmd)
    print(args.out)

if __name__ == "__main__":
    main()
