#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Commandes utilitaires (Slash Commands)
"""

import discord
import asyncio
from discord import app_commands
from discord.ext import commands


def setup_utility_commands(bot, game_session, wikipedia_service, embed_creator, formatters):
    """Configure les commandes utilitaires en slash commands"""
    
    @bot.tree.command(name='sommaire', description='Envoie le sommaire d\'un article en MP')
    @app_commands.describe(
        article='Nom de l\'article Wikipédia',
        phrases='Nombre de phrases à afficher (défaut: 2)'
    )
    async def sommaire(interaction: discord.Interaction, article: str, phrases: int = 2):
        """Envoie le sommaire d'un article en MP"""
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            channel = await interaction.user.create_dm()
            
            result = wikipedia_service.get_summary(article, phrases)
            
            if result is None:
                await interaction.followup.send(
                    f"❌ Aucun résultat pour **{article}**",
                    ephemeral=True
                )
                return
            
            article_name, summary = result
            
            embed = discord.Embed(
                title=f"📄 {article_name}",
                description=summary,
                color=0x3498db
            )
            embed.set_footer(text="Wikipédia Challenge")
            
            await channel.send(embed=embed)
            await interaction.followup.send(
                "✅ Sommaire envoyé en message privé !",
                ephemeral=True
            )
            
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Je ne peux pas vous envoyer de message privé. Vérifiez vos paramètres de confidentialité.",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"❌ Erreur : {str(e)}",
                ephemeral=True
            )
    
    @bot.tree.command(name='guide', description='Affiche le guide complet du bot')
    async def guide(interaction: discord.Interaction):
        """Affiche le guide complet du bot"""
        
        embed = embed_creator.create_guide_embed()
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name='clear', description='Supprime des messages du salon')
    @app_commands.describe(nombre='Nombre de messages à supprimer')
    @app_commands.checks.has_permissions(manage_messages=True)
    async def clear(interaction: discord.Interaction, nombre: int = 1):
        """Supprime des messages du salon"""
        try:
            await interaction.response.defer(ephemeral=True)
            deleted = await interaction.channel.purge(limit=nombre)
            await interaction.followup.send(
                f"✅ {len(deleted)} message(s) supprimé(s)",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Permissions insuffisantes !",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.followup.send(
                "❌ Impossible de supprimer tous les messages",
                ephemeral=True
            )
    
    @bot.tree.command(name='status', description='Affiche le statut actuel de la partie')
    async def status(interaction: discord.Interaction):
        """Affiche le statut actuel de la partie"""
        
        embed = embed_creator.create_status_embed(game_session, formatters, bot)
        
        await interaction.response.send_message(embed=embed)
    
    @bot.tree.command(name='leave', description='Permet de quitter la partie classée en cours')
    async def leave(interaction: discord.Interaction):
        """Permet à un joueur de quitter la partie classée en cours"""
        
        if not game_session.enabled:
            embed = embed_creator.create_error_embed(
                "Aucune partie classée n'est active."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        player_name = interaction.user.name
        
        if player_name not in game_session.members:
            embed = embed_creator.create_error_embed(
                "Vous ne faites pas partie de la partie en cours."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        game_session.members.remove(player_name)

        if game_session.winner and game_session.winner.name == player_name:
            game_session.winner = None
        
        await interaction.response.send_message(
            f"👋 **{interaction.user.display_name}** a quitté la partie classée.\n"
            f"Joueurs restants : {formatters.format_player_list(game_session.members) if game_session.members else '**Aucun**'}"
        )
        
        # Si plus personne dans la partie, la dissoudre
        if not game_session.members:
            await interaction.followup.send("🔴 **Partie dissoute** - Aucun joueur restant.")
            game_session.reset()
    
    @bot.tree.command(name='disband', description='Dissout la partie classée en cours')
    async def disband(interaction: discord.Interaction):
        """Dissout la partie classée en cours"""
        
        if not game_session.enabled:
            embed = embed_creator.create_error_embed(
                "Aucune partie classée n'est active."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        player_name = interaction.user.name
        
        if player_name not in game_session.members:
            embed = embed_creator.create_error_embed(
                "Vous ne faites pas partie de la partie en cours."
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Créer une vue avec des boutons pour confirmation
        class ConfirmView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=30.0)
                self.value = None
            
            @discord.ui.button(label='Confirmer', style=discord.ButtonStyle.danger, emoji='✅')
            async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = True
                self.stop()
                await button_interaction.response.defer()
            
            @discord.ui.button(label='Annuler', style=discord.ButtonStyle.secondary, emoji='❌')
            async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                self.value = False
                self.stop()
                await button_interaction.response.defer()
        
        embed = embed_creator.create_warning_embed(
            "Dissoudre la partie",
            f"**{interaction.user.display_name}**, voulez-vous vraiment dissoudre la partie classée ?\n"
            f"Tous les joueurs seront retirés : {formatters.format_player_list(game_session.members)}"
        )
        
        view = ConfirmView()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        await view.wait()
        
        if not view.value:
            embed = embed_creator.create_error_embed("Dissolution annulée.")
            await interaction.edit_original_response(embed=embed, view=None)
            return
        
        # Dissoudre la partie
        channel_name = "le salon"
        if game_session.channel_id:
            channel = bot.get_channel(game_session.channel_id)
            if channel:
                channel_name = f"**{channel.name}**"
        
        await interaction.edit_original_response(
            content=f"💥 **Partie dissoute** par {interaction.user.mention}\n"
                   f"La partie classée dans {channel_name} a été terminée.",
            embed=None,
            view=None
        )
        
        game_session.reset()
    
    @bot.tree.command(name='disconnect', description='Déconnecte le bot (admin seulement)')
    @app_commands.checks.has_permissions(administrator=True)
    async def disconnect(interaction: discord.Interaction):
        """Déconnecte le bot"""
        await interaction.response.send_message("👋 **WikiBot** se déconnecte...")
        await bot.close()
    
    return sommaire, guide, clear, status, leave, disband, disconnect
