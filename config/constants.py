#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Constantes et configuration du WikiBot
"""

from pathlib import Path
import json
from typing import Any, Callable, Dict

# Paliers de niveaux (XP requis)
LEVEL_THRESHOLDS = {
    1: 0, 2: 100, 3: 250, 4: 450, 5: 700,
    6: 1000, 7: 1400, 8: 1850, 9: 2350, 10: 2900,
    11: 3500, 12: 4200, 13: 5000, 14: 5900, 15: 6900,
    16: 8000, 17: 9200, 18: 10500, 19: 12000, 20: 14000
}

# Rangs par niveau
RANKS = {
    range(1, 5): {"name": "Bronze", "emoji": "🥉", "color": 0xCD7F32},
    range(5, 10): {"name": "Argent", "emoji": "🥈", "color": 0xC0C0C0},
    range(10, 15): {"name": "Or", "emoji": "🥇", "color": 0xFFD700},
    range(15, 18): {"name": "Platine", "emoji": "💍", "color": 0xE5E4E2},
    range(18, 21): {"name": "Diamant", "emoji": "💎", "color": 0xB9F2FF},
}

# Définition des achievements
ACHIEVEMENTS = {
}


# Helper to build check functions from a condition spec defined in JSON.
def _make_check(condition: Dict[str, Any]) -> Callable[[Dict[str, Any]], bool]:
    """
    Supported condition types:
      - lt: field < value
      - le: field <= value
      - gt: field > value
      - ge: field >= value
      - eq: field == value
      - len_ge: len(field) >= value (field expected to be iterable)
    """
    ctype = condition.get("type")
    field = condition.get("field")
    value = condition.get("value")

    if ctype == "lt":
        return lambda stats: stats.get(field, float('inf')) < value
    if ctype == "le":
        return lambda stats: stats.get(field, float('inf')) <= value
    if ctype == "gt":
        return lambda stats: stats.get(field, float('-inf')) > value
    if ctype == "ge":
        return lambda stats: stats.get(field, float('-inf')) >= value
    if ctype == "eq":
        return lambda stats: stats.get(field) == value
    if ctype == "len_ge":
        return lambda stats: len(stats.get(field, [])) >= value

    # Unknown condition: always False and safe.
    return lambda stats: False


_ACH_FILE = Path(__file__).parent / "achievements.json"
print(f"Loading achievements from {_ACH_FILE}")
_loaded_achievements: Dict[str, Dict[str, Any]] = {}
if _ACH_FILE.exists():
    try:
        with _ACH_FILE.open("r", encoding="utf-8") as f:
            _raw = json.load(f)
            for key, data in _raw.items():
                cond = data.pop("condition", None)
                entry = dict(data)
                entry["check"] = _make_check(cond) if cond else (lambda stats: False)
                _loaded_achievements[key] = entry
    except Exception:
        _loaded_achievements = {}
else:

    _loaded_achievements = {}

# Public achievements mapping used by the rest of the codebase.
ACHIEVEMENTS = _loaded_achievements

# Configuration des récompenses
BASE_POINTS = 310
BASE_XP_WIN = 25
BASE_XP_LOSE = 15
MIN_POINTS = 10

# Bonus temporels
TIME_BONUS_THRESHOLDS = {
    30: 30,
    60: 20,
    120: 10
}

# Bonus clics
CLICK_BONUS_THRESHOLDS = {
    3: 40,
    5: 20,
    10: 10
}