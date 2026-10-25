# api.py
from __future__ import annotations
from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from smart_grocery.io import load_pantry, save_pantry  # load_recipes not needed here
from smart_grocery.planner import plan

# ---------- Config ----------
ROOT = Path(__file__).parent
RECIPES_PATH = ROOT / "data" / "recipes.json"
PANTRY_PATH  = ROOT / "data" / "pantry.json"
PRICE_OVERRIDES_PATH: Optional[Path] = None  # set a real path later if you add overrides

# ---------- FastAPI ----------
app = FastAPI(title="Smart Grocery API")

# The front-end is served separately (python -m http.server 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Models ----------
class PlanWeekRequest(BaseModel):
    budget: float = 50.0
    max_time: int = 45
    k_new: int = 2
    max_calories_per_meal: Optional[int] = None
    strategy: str = "knapsack_max_recipes"

# ---------- Helpers ----------
def _coerce_items_from_any(payload: Any) -> List[str]:
    """Accepts JSON dict/list/str or form-encoded 'items' and returns a normalized string list."""
    items: List[str] = []

    if isinstance(payload, dict):
        val = payload.get("items") or payload.get("pantry") or payload.get("value") or payload.get("list")
        if isinstance(val, list):
            items = [str(x) for x in val]
        elif isinstance(val, str):
            items = [s.strip() for s in val.replace("\n", ",").split(",") if s.strip()]
    elif isinstance(payload, list):
        items = [str(x) for x in payload]
    elif isinstance(payload, str):
        items = [s.strip() for s in payload.replace("\n", ",").split(",") if s.strip()]

    return [s.lower() for s in items if s]

def _coerce_recipe_for_frontend(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": r.get("name", "Untitled"),
        "time_min": int(r.get("time_min", 0)),
        "calories": int(r.get("calories", 0)),
        "missing": [
            {"name": m.get("name", ""), "price": float(m.get("price", 0.0))}
            for m in r.get("missing", [])
        ],
        "existing": [str(x) for x in r.get("existing", [])],
        "est_total_cost": float(r.get("est_total_cost", 0.0)),
        "ingredients": [str(x) for x in r.get("ingredients", [])],
        "instructions": [str(x) for x in r.get("instructions", [])],
    }

# ---------- Routes ----------
@app.get("/health")
def health():
    return {
        "ok": True,
        "recipes_path": str(RECIPES_PATH),
        "pantry_size": len(load_pantry(PANTRY_PATH)),
    }

@app.get("/pantry")
def get_pantry():
    return {"items": load_pantry(PANTRY_PATH)}

@app.put("/pantry")
async def put_pantry(request: Request):
    # Try JSON first
    body: Any = None
    try:
        body = await request.json()
    except Exception:
        body = None

    items = _coerce_items_from_any(body)

    # If JSON didn’t yield items, try form
    if not items:
        try:
            form = await request.form()
            val = form.get("items")
            if val:
                items = _coerce_items_from_any(val)
        except Exception:
            pass

    # Save
    save_pantry(PANTRY_PATH, items)
    return {"ok": True, "size": len(items), "items": items}

@app.post("/plan-week-server")
def plan_week_server(req: PlanWeekRequest):
    if not RECIPES_PATH.exists():
        raise HTTPException(status_code=500, detail=f"Missing recipes at {RECIPES_PATH}")

    pantry_items = load_pantry(PANTRY_PATH)

    try:
        res = plan(
            recipes_path=str(RECIPES_PATH),
            pantry_items=pantry_items,
            budget=req.budget,
            max_time=req.max_time,
            k_new=req.k_new,
            strategy=req.strategy,
            price_overrides_path=str(PRICE_OVERRIDES_PATH) if PRICE_OVERRIDES_PATH else None,
            max_calories_per_meal=req.max_calories_per_meal,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    week_plan = [_coerce_recipe_for_frontend(r) for r in res.get("recipes", [])]
    return {
        "week_plan": week_plan,
        "metrics": res.get("metrics", {}),
        "grocery_list": res.get("grocery_list", []),
    }
