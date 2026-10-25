# Smart Grocery — Meal Planner (FastAPI + Vanilla JS)

A minimal, working meal‑planner that:
- Saves your pantry
- Generates a 7‑day plan from your pantry & constraints
- Produces a consolidated shopping list
- Shows ingredients + step‑by‑step instructions per recipe

The stack is **FastAPI** (backend) and a **static web front‑end** (HTML/CSS/JS).

---

## 1) Project layout

```
GroceryProject/
├─ api.py                  # FastAPI app (CORS enabled)
├─ smart_grocery/
│  ├─ planner.py           # planning/selection logic
│  ├─ filtering.py         # ranking, pantry-first, budget/time filters
│  ├─ models.py            # dataclasses/pydantic models
│  ├─ io.py                # load/save recipes & pantry
│  └─ ...                  # metrics, normalize, etc.
├─ data/
│  ├─ recipes.sample.json  # recipe catalog (expand me!)
│  └─ pantry.json          # saved pantry (auto-created)
└─ web/
   ├─ index.html           # UI screens (Pantry / Plan / Shop)
   ├─ app.js               # front-end logic & API calls
   └─ styles.css           # color palette & layout
```

---

## 2) Requirements

- macOS or Linux (Windows WSL ok)
- Python **3.10+** (3.11/3.13 work)
- `pip`

Optional (for a quick static server): no Node needed; we use Python’s `http.server`.

---

## 3) Setup

From the project root (`GroceryProject/`):

```bash
# 1) Create & activate a virtual env
python3 -m venv .venv
source .venv/bin/activate   # (Windows: .venv\Scripts\activate)

# 2) Install deps
python -m pip install --upgrade pip
pip install fastapi uvicorn pydantic python-multipart

# 3) Run the API on port 8000
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

Verify it’s up:
```bash
curl -i http://127.0.0.1:8000/health
# should return JSON with ok:true
```

---

## 4) Run the front‑end (no build tools)

Serve the `web/` folder with a static server at **http://127.0.0.1:5173/**

```bash
# In another terminal
cd web
python3 -m http.server 5173
# visit: http://127.0.0.1:5173/
```

> Tip: If `python` isn’t found, use `python3`. If port 5173 is busy, change it (e.g., 5174).

---

## 5) Using the app

1. **Pantry tab**: paste or add items (e.g., `eggs, onion, garlic, pasta, olive oil, salt, pepper`) and click **Save**.  
2. **Plan Week tab**: set Budget/Max Time/RMR@k/Max Calories and click **Plan Week**.  
3. Click a day card to open the recipe modal (ingredients + instructions).  
4. **Shop tab**: view/download your consolidated shopping list (CSV), or export Week JSON.

---

## 6) API reference

### Health
```
GET /health
200 OK
{"ok": true, "recipes_path": ".../data/recipes.sample.json", "pantry_size": 0}
```

### Pantry
Two JSON formats are accepted.

- **Array** (fastest):
```
PUT /pantry
Content-Type: application/json

["eggs","onion","garlic","pasta","olive oil","salt","pepper"]
```

- **Object** (also supported):
```
PUT /pantry
Content-Type: application/json

{"items":["eggs","onion","garlic"]}
```

Response:
```
{"ok": true, "size": 7, "items": ["eggs","onion", ...]}
```

### Plan week
```
POST /plan-week-server
Content-Type: application/json

{
  "budget": 30,
  "max_time": 30,
  "k_new": 2,
  "max_calories_per_meal": 600,
  "strategy": "knapsack_max_recipes"
}
```

Response (excerpt):
```json
{
  "week_plan": [ { "name": "Omelette", "time_min": 10, ... }, ... ],
  "grocery_list": [ {"name":"tomato","est_price":2.0}, ... ],
  "metrics": {
    "strategy":"knapsack_max_recipes",
    "target_budget":30.0,
    "total_spend":25.4,
    "budget_adherence_percent":15.3,
    "rmr_percent_at_k_all":25.0,
    "rmr_percent_at_k_chosen":37.5
  }
}
```

---

## 7) Add more recipes

Edit `data/recipes.sample.json`. Each recipe object supports strings for ingredients/instructions (simple) and the app will normalize them. Example:

```json
[
  {
    "name": "Simple Pasta",
    "time_min": 20,
    "calories": 520,
    "ingredients": ["pasta", "olive oil", "garlic", "parmesan", "salt", "pepper"],
    "instructions": ["Boil pasta", "Saute garlic in oil", "Toss pasta", "Add parmesan", "Season"]
  },
  {
    "name": "Vegetable Stir Fry",
    "time_min": 18,
    "calories": 420,
    "ingredients": ["rice", "soy sauce", "garlic", "ginger", "bell pepper", "broccoli", "sesame oil"],
    "instructions": ["Cook rice", "Stir-fry veg", "Add sauce", "Serve with rice"]
  }
]
```

> **Synonyms & pantry‑first:** The app normalizes common aliases (e.g., `onions` → `onion`, `cooked rice` ↔︎ `rice`) so items you have are not marked as missing when they are equivalent.

---

## 8) Color palette

The UI uses the palette:
```
#5F0F40  #9A031E  #FB8B24  #E36414  #0F4C5C
```
Feel free to tweak in `web/styles.css`.

---

## 9) Troubleshooting

- **ModuleNotFoundError: fastapi**  
  You’re not in the venv. Run `source .venv/bin/activate` and `pip install fastapi uvicorn pydantic`.

- **422 Unprocessable Content on PUT /pantry**  
  Payload shape doesn’t match. Send either a JSON array of strings or `{"items":[...]}` and set header `Content-Type: application/json`.

- **500 on /plan-week-server with “string indices must be integers”**  
  Your `data/recipes.sample.json` must be a JSON *array* of objects. Ingredients/instructions can be arrays of strings (see example above).

- **Port in use (8000/5173)**  
  Change ports or kill the process:  
  `lsof -i :8000 -nP | awk 'NR>1 {print $2}' | xargs -r kill -9`

- **CORS/Network issues in browser**  
  Make sure API is on `http://127.0.0.1:8000` and front‑end is from `http://127.0.0.1:5173`. The API already allows these origins.

---

## 10) Deploy notes (optional)

- **Backend**: Deploy `api.py` (FastAPI) on Render/Railway/Fly.io.  
- **Frontend**: Host `web/` as static files on Netlify/GitHub Pages. Update `API_BASE` in `web/app.js` to your hosted API URL.

---

## 11) Quick demo (curl)

```bash
# Save pantry
curl -s -X PUT http://127.0.0.1:8000/pantry \
  -H "Content-Type: application/json" \
  -d '["eggs","onion","garlic","pasta","olive oil","salt","pepper"]' | jq .

# Plan week
curl -s -X POST http://127.0.0.1:8000/plan-week-server \
  -H "Content-Type: application/json" \
  -d '{"budget":30,"max_time":30,"k_new":2,"max_calories_per_meal":600,"strategy":"knapsack_max_recipes"}' | jq .
```

---
