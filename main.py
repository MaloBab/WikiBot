#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
WikiBot - Bot Discord pour le Wikipédia Challenge
Point d'entrée principal
"""

import discord
import wikipedia
from discord.ext import commands
from pathlib import Path

# Imports de configuration
from config.settings import TOKEN, DATA_DIR, WIKI_LANG, COMMAND_PREFIX, BOT_DESCRIPTION, BOT_ACTIVITY
from config.constants import (
    LEVEL_THRESHOLDS, RANKS, ACHIEVEMENTS, BASE_POINTS, BASE_XP_WIN, 
    BASE_XP_LOSE, MIN_POINTS, TIME_BONUS_THRESHOLDS, CLICK_BONUS_THRESHOLDS
)

# Imports des modèles
from models.timer import Timer
from models.game_session import GameSession

# Imports des repositories
from repositories.player_repository import PlayerRepository

# Imports des services
from services.player_service import PlayerService
from services.game_service import GameService
from services.stats_service import StatsService
from services.wikipedia_service import WikipediaService

# Imports des utilitaires
from utils.formatters import Formatters
from utils.calculators import Calculators
from utils.validators import Validators

# Imports de l'UI
from ui.embeds import EmbedCreator

# Imports des événements
from events.ready_event import on_ready_handler
from events.reaction_event import on_reaction_add_handler
from events.voice_event import on_voice_state_update_handler

# Imports des commandes
from commands.game_commands import setup_game_commands
from commands.stats_commands import setup_stats_commands
from commands.utility_commands import setup_utility_commands


def main():
    """Point d'entrée principal de l'application"""
    
    # Configuration de Wikipedia
    wikipedia.set_lang(WIKI_LANG)
    
    # Configuration Discord
    intents = discord.Intents.default()
    intents.members = True
    intents.messages = True
    intents.reactions = True
    intents.guilds = True
    intents.message_content = True
    
    bot = commands.Bot(
        command_prefix=COMMAND_PREFIX,
        description=BOT_DESCRIPTION,
        intents=intents,
        help_command=None
    )
    
    game_session = GameSession()
    
    player_repository = PlayerRepository(DATA_DIR)
    
    constants = {
        'LEVEL_THRESHOLDS': LEVEL_THRESHOLDS,
        'RANKS': RANKS,
        'ACHIEVEMENTS': ACHIEVEMENTS,
        'BASE_POINTS': BASE_POINTS,
        'BASE_XP_WIN': BASE_XP_WIN,
        'BASE_XP_LOSE': BASE_XP_LOSE,
        'MIN_POINTS': MIN_POINTS,
        'TIME_BONUS_THRESHOLDS': TIME_BONUS_THRESHOLDS,
        'CLICK_BONUS_THRESHOLDS': CLICK_BONUS_THRESHOLDS
    }

    player_service = PlayerService(player_repository, constants)
    stats_service = StatsService(constants)
    game_service = GameService(player_service, stats_service)
    wikipedia_service = WikipediaService(WIKI_LANG)

    formatters = Formatters()
    calculators = Calculators()
    validators = Validators()

    embed_creator = EmbedCreator()
    
    # Configuration des événements
    @bot.event
    async def on_ready():
        await bot.change_presence(activity=discord.Game(BOT_ACTIVITY))
        await on_ready_handler(bot)
    
    @bot.event
    async def on_reaction_add(reaction, user):
        # Récupérer la commande way
        way_cmd = None
        for cmd in bot.commands:
            if cmd.name == 'way':
                way_cmd = cmd
                break
        
        await on_reaction_add_handler(
            reaction, user, bot, game_session, 
            player_service, way_cmd
        )
    
    @bot.event
    async def on_voice_state_update(member, before, after):
        await on_voice_state_update_handler(member, before, after, game_session, bot)
    
    # Configuration des commandes
    setup_game_commands(
        bot, game_session, player_service, game_service, 
        wikipedia_service, embed_creator, formatters, validators
    )
    
    setup_stats_commands(
        bot, player_service, embed_creator, formatters
    )
    
    setup_utility_commands(
        bot, game_session, wikipedia_service, embed_creator, formatters
    )
    
    # Lancement du bot
    print("Démarrage de WikiBot...")
    bot.run(TOKEN)


if __name__ == "__main__":
    main()