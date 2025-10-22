#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Paramètres de configuration du bot
"""

from pathlib import Path

# Lecture du token
with open("TOKEN.dat", "r") as token_file:
    TOKEN = token_file.read().strip()

# Répertoires de données
DATA_DIR = Path("../Joueurs")
DATA_DIR.mkdir(exist_ok=True)

# Configuration Wikipedia
WIKI_LANG = "fr"
WIKI_RANDOM_PAGES = 10
MAX_GENERATION_ATTEMPTS = 10

# Configuration Discord
BOT_DESCRIPTION = "Wikipédia Challenge - Un bot Discord pour jouer au Wikipédia Challenge"
BOT_ACTIVITY = f'/guide'
