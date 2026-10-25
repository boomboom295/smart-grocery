import json, sys, os, re

def load_any(path):
    with open(path, "r") as f:
        data = json.load(f)
    # Accept either: dict {"recipes":[...], "prices":{...}} or plain list [...]
    if isinstance(data, dict):
        recipes = data.get("recipes", [])
        prices  = data.get("prices", {})
    elif isinstance(data, list):
        recipes = data
        prices  = {}
    else:
        raise ValueError(f"Unsupported JSON at {path}")
    # Normalize fields a bit
    normd = []
    for r in recipes:
        if not isinstance(r, dict): continue
        name = (r.get("name") or r.get("title") or "").strip()
        if not name: continue
        time_min = r.get("time_min") or r.get("total_time") or r.get("minutes")
        calories = r.get("calories")
        ings = r.get("ingredients") or r.get("ingr") or r.get("ing_list") or []
        instr = r.get("instructions") or r.get("directions") or []
        # make sure lists are strings
        ings = [str(x).strip().lower() for x in ings if str(x).strip()]
        instr = [str(x).strip() for x in instr if str(x).strip()]
        try:
            time_min = int(time_min) if str(time_min).isdigit() else None
        except: time_min = None
        try:
            calories = int(calories) if str(calories).isdigit() else None
        except: calories = None
        normd.append({
            "name": name[:120],
            "time_min": time_min,
            "calories": calories,
            "ingredients": ings,
            "instructions": instr
        })
    return {"recipes": normd, "prices": prices}

def save_catalog(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)

def main():
    if len(sys.argv) < 3:
        print("usage: python tools/add_recipes.py <base.json> <add.json>")
        sys.exit(1)

    base_path = sys.argv[1]
    add_path  = sys.argv[2]

    # Load both files (robust to list/dict schemas)
    base = load_any(base_path)
    add  = load_any(add_path)

    base_recipes = base["recipes"]
    base_prices  = base["prices"] or {}

    # Build dedupe set on lowercase name
    seen = { r["name"].strip().lower() for r in base_recipes if r.get("name") }

    added = 0
    for r in add["recipes"]:
        key = r["name"].strip().lower()
        if not key or key in seen: 
            continue
        base_recipes.append(r)
        seen.add(key)
        added += 1
        # backfill prices for new ingredients if missing
        for ing in r.get("ingredients", []):
            if ing not in base_prices:
                base_prices[ing] = 1.0  # default fallback

    # Optional: ensure a few common pantry items are priced
    for k, v in {
        "salt":0.1, "pepper":0.1, "olive oil":0.5, "oil":0.4, "onion":0.6, "garlic":0.5,
        "tomato":0.9, "pasta":1.6, "rice":1.5, "eggs":2.9, "egg":2.9, "parmesan":3.2,
        "cheddar":3.0, "broccoli":1.4, "carrot":0.6, "bell pepper":1.0, "soy sauce":0.5,
        "yogurt":1.0, "tortilla":1.8, "chickpeas":1.2, "lentils":1.3, "pesto":3.0
    }.items():
        base_prices.setdefault(k, v)

    out = {"recipes": base_recipes, "prices": base_prices}
    save_catalog(base_path, out)
    print(f"OK: merged {added} new recipes → now {len(base_recipes)} recipes, {len(base_prices)} priced items")

if __name__ == "__main__":
    main()
