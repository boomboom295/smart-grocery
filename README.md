# Smart Grocery: budget-aware meal planner

Tell it what's in your pantry, your grocery budget, and how long you're willing to cook. It picks a set of recipes that fits the budget and gives you one combined shopping list.

```
pantry + budget + time/calorie limits
   ─► normalize ingredient names   ("chopped red onions" → "onion")
   ─► price each recipe by what you'd still have to buy
   ─► filter by cooking time and calories
   ─► choose recipes with a selection strategy (greedy or 0/1 knapsack)
   ─► week plan + consolidated shopping list + metrics
```

It has a **FastAPI** backend, a **plain HTML/CSS/JS** front end (no build step), and a **command-line** version. It started as my ECE 57000 course project at Purdue (Fall 2025).

## Selection strategies

| Strategy | What it optimizes |
|---|---|
| `greedy_cost` | Adds the cheapest recipes first until the budget runs out |
| `greedy_low_missing` | Adds recipes that need the fewest new ingredients first, so it uses the most of your pantry |
| `knapsack_max_recipes` | Dynamic-programming 0/1 knapsack (costs in cents). Finds the largest number of recipes that fit the budget, and breaks ties toward fewer new ingredients. |

Example output (`python main.py --compare --budget 20`, 43 recipes, the sample pantry):

| strategy | #recipes | spend | budget deviation % | RMR@2 (chosen) |
|---|---:|---:|---:|---:|
| greedy_cost | 12 | $18.60 | 7.0 | 75.0% |
| greedy_low_missing | 11 | $18.10 | 9.5 | 100.0% |
| knapsack_max_recipes | 12 | $19.50 | 2.5 | 83.3% |

**Metrics**
- **RMR@k** (recipe match rate): the percent of recipes that need at most *k* new items.
- **Budget deviation**: how far the spend lands from the target budget.

## Run it

Requires Python 3.10+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

**Web app** (two terminals):

```bash
uvicorn api:app --port 8000          # API
cd web && python3 -m http.server 5173 # front end -> open http://127.0.0.1:5173
```

Use the app in three tabs:
1. **Pantry:** add the items you have.
2. **Plan Week:** set the budget, time and calorie limits, then pick a strategy.
3. **Shop:** download the shopping list as CSV.

**Command line:**

```bash
python main.py --budget 15 --max_time 20 --strategy knapsack_max_recipes
python main.py --compare --budget 20     # every strategy side by side -> data/compare.md
```

**Tests:**

```bash
pytest
```

The tests check the knapsack result against brute force, ingredient normalization, the budget, time and calorie limits, and the API routes.

## API

| Method | Route | Body |
|---|---|---|
| GET | `/health` | none |
| GET / PUT | `/pantry` | `["eggs", "onion"]` or `{"items": [...]}` |
| POST | `/plan-week-server` | `{"budget": 30, "max_time": 30, "k_new": 2, "max_calories_per_meal": 600, "strategy": "knapsack_max_recipes"}` |

`/plan-week-server` returns three fields:
- `week_plan`: up to 7 recipes, each with ingredients, instructions, what you already have, and what's missing with prices.
- `grocery_list`: the combined shopping list.
- `metrics`: the numbers described above.

## Project layout

| Path | What it does |
|---|---|
| `api.py` | FastAPI app |
| `main.py` | Command-line planner and strategy comparison |
| `smart_grocery/normalize.py` | Canonical ingredient names: plurals, prep words, aliases |
| `smart_grocery/filtering.py` | Price map, per-recipe cost view, time and calorie filters, ranking |
| `smart_grocery/selection.py` | Greedy and knapsack selection |
| `smart_grocery/planner.py` | Runs the full pipeline |
| `smart_grocery/io.py` | Loads and saves recipes, pantry and price overrides |
| `web/` | Front end (Pantry / Plan / Shop tabs) |
| `tools/add_recipes.py` | Merges another recipe JSON into the catalog |
| `data/recipes.json` | Recipe catalog (43 recipes) |

## Adding recipes

Add objects to `data/recipes.json`:

```json
{"name": "Simple Pasta", "time_min": 20, "calories": 520,
 "ingredients": ["pasta", "olive oil", "garlic", "parmesan"],
 "instructions": ["Boil pasta", "Saute garlic in oil", "Toss and top with parmesan"]}
```

To change prices, pass a JSON file like `{"parmesan": 4.0}` with `--price_overrides`, or add a `"prices"` object to the catalog.

## Limitations and next steps

- Prices are fixed estimates per ingredient. Quantities aren't modeled yet, so the planner assumes you buy one unit of each missing item.
- A store-price API and a nutrition API would make the costs and calories real.
- Possible additions: multi-objective selection (cost + nutrition + variety) and avoiding repeated recipes within a week.
