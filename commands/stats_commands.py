#! /usr/bin/python
# -*- coding: utf-8 -*-

import discord
from discord import app_commands
from discord.ext import commands


def setup_stats_commands(bot, player_service, embed_creator, formatters):
    """Configure les commandes de statistiques en slash commands"""

    @bot.tree.command(name='stats', description='Affiche les statistiques détaillées d\'un joueur')
    @app_commands.describe(joueur='Nom du joueur (laissez vide pour voir vos stats)')
    async def stats(interaction: discord.Interaction, joueur: str = None):
        """Affiche les statistiques détaillées d'un joueur"""
        
        if joueur is None:
            joueur = interaction.user.name
        
        player_data = player_service.get_player(joueur)
        
        if not player_data:
            await interaction.response.send_message(
                f"❌ Le joueur **{joueur}** n'existe pas !",
                ephemeral=True
            )
            return
        
        # Obtenir le rang
        rank_info = player_service.get_rank_info(player_data['level'])
        
        # Créer l'embed
        embed = embed_creator.create_stats_embed(joueur, player_data, rank_info, formatters)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name='achievements', description='Affiche les succès d\'un joueur')
    @app_commands.describe(joueur='Nom du joueur (laissez vide pour voir vos succès)')
    async def achievements(interaction: discord.Interaction, joueur: str = None):
        """Affiche les achievements d'un joueur"""
        
        if joueur is None:
            joueur = interaction.user.name
        
        player_data = player_service.get_player(joueur)
        
        if not player_data:
            await interaction.response.send_message(
                f"❌ Le joueur **{joueur}** n'existe pas !",
                ephemeral=True
            )
            return
        
        rank_info = player_service.get_rank_info(player_data['level'])
        
        embed = embed_creator.create_achievements_embed(joueur, player_data, rank_info, formatters)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name='scoreboard', description='Affiche le classement des meilleurs joueurs')
    async def scoreboard(interaction: discord.Interaction):
        """Affiche le classement des meilleurs joueurs"""
        
        players = player_service.get_all_players()
        
        if not players:
            await interaction.response.send_message(
                "Aucun joueur enregistré !",
                ephemeral=True
            )
            return
        
        embed = embed_creator.create_scoreboard_embed(players, formatters)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name='leaderboard', description='Affiche différents classements')
    @app_commands.describe(categorie='Catégorie de classement')
    @app_commands.choices(categorie=[
        app_commands.Choice(name='Points', value='points'),
        app_commands.Choice(name='Niveau', value='level'),
        app_commands.Choice(name='Win Rate', value='winrate'),
        app_commands.Choice(name='XP', value='xp')
    ])
    async def leaderboard(interaction: discord.Interaction, categorie: str = "points"):
        """Affiche différents classements"""
        
        players = player_service.get_all_players(sort_by=categorie)
        
        if not players:
            await interaction.response.send_message(
                "Aucun joueur enregistré !",
                ephemeral=True
            )
            return
        
        embed = embed_creator.create_leaderboard_embed(players, categorie, formatters)
        
        await interaction.response.send_message(embed=embed)
    
    return stats, achievements, scoreboard, leaderboard