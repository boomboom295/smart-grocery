# smart_grocery/io.py
from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

from .models import Ingredient, Recipe


def _coerce_recipe_struct(r: Dict[str, Any]) -> Dict[str, Any]:
    """Make recipe dict tolerant: accept either dicts or strings for ingredients/instructions."""
    name = str(r.get("name", "Untitled"))

    # Ingredients: allow list of dicts (with name/qty/unit) OR list of strings
    raw_ings = r.get("ingredients", [])
    ings: List[Ingredient] = []
    if isinstance(raw_ings, list):
        for i in raw_ings:
            if isinstance(i, dict):
                ings.append(Ingredient(
                    name=str(i.get("name", "")),
                    qty=float(i.get("qty", 0.0) or 0.0),
                    unit=str(i.get("unit", "")),
                ))
            else:
                # string or other -> just name
                ings.append(Ingredient(name=str(i)))
    else:
        # single string
        ings.append(Ingredient(name=str(raw_ings)))

    # Simple numeric attrs
    time_min = int(r.get("time_min", r.get("time", 0)) or 0)
    calories = int(r.get("calories", 0) or 0)

    # Instructions: allow list of strings or single string
    instr_raw = r.get("instructions", [])
    if isinstance(instr_raw, list):
        instructions = [str(x) for x in instr_raw]
    elif isinstance(instr_raw, str):
        instructions = [instr_raw]
    else:
        instructions = []

    return {
        "name": name,
        "ingredients": ings,
        "time_min": time_min,
        "calories": calories,
        "instructions": instructions,
    }

def load_recipes(path: str | Path) -> List[Recipe]:
    p = Path(path)
    with p.open("r") as f:
        data = json.load(f)

    # allow either {"recipes":[...]} or a bare list [...]
    if isinstance(data, dict) and "recipes" in data:
        items = data["recipes"]
    else:
        items = data

    out: List[Recipe] = []
    for r in items:
        rr = _coerce_recipe_struct(r)
        out.append(Recipe(**rr))
    return out

def load_catalog_prices(path: str | Path) -> Dict[str, float]:
    """Prices stored in the catalog itself ({"recipes": [...], "prices": {...}}), if any."""
    with Path(path).open("r") as f:
        data = json.load(f)
    prices = data.get("prices", {}) if isinstance(data, dict) else {}
    return {str(k).lower(): float(v) for k, v in prices.items()}


def load_pantry(path: str | Path) -> List[str]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open("r") as f:
        data = json.load(f)
    # accept {"items":[...]}, {"pantry":[...]} or [...]
    if isinstance(data, dict):
        data = data.get("items", data.get("pantry", []))
    if isinstance(data, list):
        return [str(x).lower() for x in data]
    return []

def save_pantry(path: str | Path, items: List[str]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w") as f:
        json.dump({"items": [str(x).lower() for x in items]}, f, indent=2)

def load_price_overrides(path: Optional[str | Path]) -> Dict[str, float]:
    """Return {ingredient_name: price} or {} if no file or invalid."""
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r") as f:
            data = json.load(f)
        if isinstance(data, dict):
            # normalize to float
            return {str(k).lower(): float(v) for k, v in data.items()}
        return {}
    except Exception:
        return {}
