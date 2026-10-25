from typing import List
from .normalize import normalize_ingredient

def normalize_pantry(pantry_items: List[str]) -> List[str]:
    return sorted({normalize_ingredient(p) for p in pantry_items})

def pantry_contains(pantry_norm: List[str], ingredient_norm: str) -> bool:
    return ingredient_norm in pantry_norm
