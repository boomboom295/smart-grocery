import csv
from typing import Dict, List

def to_markdown(res: Dict) -> str:
    lines = []
    lines.append("# Smart Grocery Plan")
    lines.append("")
    lines.append("## Metrics")
    m = res["metrics"]
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    for k in ["strategy","target_budget","total_spend","budget_adherence_percent","rmr_percent_at_k_all","rmr_percent_at_k_chosen"]:
        lines.append(f"| {k} | {m[k]} |")
    lines.append("")
    lines.append("## Chosen Recipes")
    lines.append("| recipe | time_min | calories | est_total_cost | missing | existing |")
    lines.append("|---|---:|---:|---:|---|---|")
    for r in res["recipes"]:
        miss = ", ".join([x["name"] for x in r["missing"]]) if r["missing"] else "-"
        ex = ", ".join(r["existing"]) if r["existing"] else "-"
        lines.append(f"| {r['name']} | {r['time_min']} | {r['calories']} | {r['est_total_cost']} | {miss} | {ex} |")
    lines.append("")
    lines.append("## Grocery List")
    lines.append("| item | est_price |")
    lines.append("|---|---:|")
    for g in res["grocery_list"]:
        lines.append(f"| {g['name']} | {g['est_price']} |")
    lines.append("")
    return "\n".join(lines)

def write_markdown(res: Dict, path: str) -> None:
    s = to_markdown(res)
    with open(path, "w") as f:
        f.write(s)

def write_csvs(res: Dict, grocery_csv: str, recipes_csv: str) -> None:
    with open(grocery_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name","est_price"])
        for g in res["grocery_list"]:
            w.writerow([g["name"], g["est_price"]])
    with open(recipes_csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name","time_min","calories","est_total_cost","missing_count"])
        for r in res["recipes"]:
            w.writerow([r["name"], r["time_min"], r["calories"], r["est_total_cost"], len(r["missing"])])
