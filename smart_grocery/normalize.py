# smart_grocery/normalize.py
import re

# Words that don't change the core ingredient identity
_PREP_WORDS = {
    "chopped","diced","minced","sliced","grated","shredded","crushed","mashed",
    "cooked","uncooked","boiled","steamed","roasted","baked","fried","sauteed",
    "fresh","frozen","canned","drained","rinsed","peeled","ripe","raw",
    "small","medium","large"
}

# Simple singularization for common plurals
_PLURAL_ENDINGS = [
    ("ies","y"),   # berries -> berry
    ("oes","o"),
    ("ves","f"),   # loaves -> loaf (rough)
    ("s",""),      # onions -> onion
]

# Synonym/alias map -> canonical
_ALIASES = {
    # onions
    "onions":"onion",
    "red onion":"onion",
    "yellow onion":"onion",
    "white onion":"onion",
    "spring onion":"green onion",
    "scallion":"green onion",
    "scallions":"green onion",

    # rice
    "cooked rice":"rice",
    "basmati rice":"rice",
    "brown rice":"rice",
    "jasmine rice":"rice",
    "long grain rice":"rice",
    "short grain rice":"rice",

    # oils
    "veg oil":"oil",
    "vegetable oil":"oil",
    "olive oil":"olive oil",

    # garlic forms
    "garlic clove":"garlic",
    "garlic cloves":"garlic",

    # peppers
    "bell pepper":"pepper",
    "bell peppers":"pepper",

    # pasta shapes collapse (optional)
    "spaghetti":"pasta",
    "penne":"pasta",
    "macaroni":"pasta",
    "fusilli":"pasta",
}

_WHITESPACE_RE = re.compile(r"\s+")

def _singularize(word: str) -> str:
    w = word
    for end, rep in _PLURAL_ENDINGS:
        if w.endswith(end) and len(w) > len(end):
            return w[: -len(end)] + rep
    return w

def norm(s: str) -> str:
    """
    Canonicalize an ingredient or pantry item:
    - lowercase
    - strip punctuation
    - remove common prep adjectives
    - collapse whitespace
    - singularize simple plurals
    - apply alias map
    """
    x = (s or "").strip().lower()
    x = re.sub(r"[^\w\s-]", " ", x)
    # remove prep words as full tokens
    tokens = [t for t in _WHITESPACE_RE.split(x) if t and t not in _PREP_WORDS]
    x = " ".join(tokens)

    # alias lookup first (handles multiword cases like "cooked rice")
    if x in _ALIASES:
        x = _ALIASES[x]

    # singularize last token if it’s a simple plural
    parts = x.split()
    if parts:
        parts[-1] = _singularize(parts[-1])
        x = " ".join(parts)

    # second alias pass after singularization
    if x in _ALIASES:
        x = _ALIASES[x]

    return x
