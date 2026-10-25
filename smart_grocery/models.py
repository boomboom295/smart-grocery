from dataclasses import dataclass, field
from typing import List

@dataclass
class Ingredient:
    name: str
    qty: float = 0.0
    unit: str = ""

@dataclass
class Recipe:
    name: str
    time_min: int = 0
    calories: int = 0
    ingredients: List[Ingredient] = field(default_factory=list)
    instructions: List[str] = field(default_factory=list)

@dataclass
class PricedIngredient:
    name: str
    price: float

@dataclass
class RecipeCostView:
    recipe: Recipe
    missing: List[PricedIngredient] = field(default_factory=list)
    existing: List[str] = field(default_factory=list)
    est_total_cost: float = 0.0
