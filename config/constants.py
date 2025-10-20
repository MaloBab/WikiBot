#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Constantes et configuration du WikiBot
"""

from pathlib import Path

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
    "eclair": {
        "name": "⚡ Éclair",
        "description": "Gagner en moins de 30 secondes",
        "xp": 50,
        "check": lambda stats: stats.get("best_time", float('inf')) < 30
    },
    "minimaliste": {
        "name": "🎯 Minimaliste",
        "description": "Gagner en moins de 3 clics",
        "xp": 100,
        "check": lambda stats: stats.get("best_clicks", float('inf')) <= 3
    },
    "marathon": {
        "name": "🏃 Marathon",
        "description": "Jouer 10 parties d'affilée",
        "xp": 75,
        "check": lambda stats: stats.get("current_streak", 0) >= 10
    },
    "explorateur": {
        "name": "🗺️ Explorateur",
        "description": "Visiter 100 articles uniques",
        "xp": 150,
        "check": lambda stats: len(stats.get("articles_visited", [])) >= 100
    },
    "perfectionniste": {
        "name": "👑 Perfectionniste",
        "description": "10 victoires consécutives",
        "xp": 200,
        "check": lambda stats: stats.get("win_streak", 0) >= 10
    },
    "debutant": {
        "name": "🌱 Débutant",
        "description": "Jouer votre première partie",
        "xp": 10,
        "check": lambda stats: stats.get("parties_jouees", 0) >= 1
    },
    "veterane": {
        "name": "🎖️ Vétéran",
        "description": "Jouer 50 parties",
        "xp": 100,
        "check": lambda stats: stats.get("parties_jouees", 0) >= 50
    },
    "champion": {
        "name": "🏆 Champion",
        "description": "Gagner 25 parties",
        "xp": 150,
        "check": lambda stats: stats.get("parties_gagnees", 0) >= 25
    },
    "rapide": {
        "name": "💨 Rapide",
        "description": "Temps moyen inférieur à 60 secondes",
        "xp": 75,
        "check": lambda stats: stats.get("temps_moyen", float('inf')) < 60
    },
    "efficace": {
        "name": "🎲 Efficace",
        "description": "Moyenne de clics inférieure à 5",
        "xp": 75,
        "check": lambda stats: stats.get("moyenne_clics", float('inf')) < 5
    }
}

# Configuration des récompenses
BASE_POINTS = 300
BASE_XP_WIN = 20
BASE_XP_LOSE = 5
MIN_POINTS = 10

# Bonus temporels
TIME_BONUS_THRESHOLDS = {
    30: 15,
    60: 10,
    120: 5
}

# Bonus clics
CLICK_BONUS_THRESHOLDS = {
    3: 20,
    5: 10,
    10: 5
}