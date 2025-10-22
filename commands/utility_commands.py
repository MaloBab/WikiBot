#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Commandes utilitaires
"""

import discord
import asyncio
from discord.ext import commands


def setup_utility_commands(bot, game_session, wikipedia_service, embed_creator, formatters):
    """Configure les commandes utilitaires"""
    
    @bot.command(name='sommaire')
    async def sommaire(ctx, *, args):
        """Envoie le sommaire d'un article en MP"""
        
        # Séparer les arguments
        parts = args.rsplit(maxsplit=1)
        
        # Vérifier si le dernier argument est un nombre
        if len(parts) == 2 and parts[1].isdigit():
            article = parts[0]
            nb_phrases = int(parts[1])
        else:
            article = args
            nb_phrases = 2
        
        try:
            channel = await ctx.author.create_dm()
            searching_msg = await channel.send("🔍 Recherche en cours...")
            
            result = wikipedia_service.get_summary(article, nb_phrases)
            
            if result is None:
                await channel.send(f"❌ Aucun résultat pour **{article}**")
                await searching_msg.delete()
                await ctx.message.delete()
                return
            
            article_name, summary = result
            
            embed = discord.Embed(
                title=f"📄 {article_name}",
                description=summary,
                color=0x3498db
            )
            embed.set_footer(text="Wikipédia Challenge")
            
            await channel.send(embed=embed)
            await searching_msg.delete()
            await ctx.message.delete()
            
        except Exception as e:
            await channel.send(f"❌ Erreur : {str(e)}")
    
    @bot.command(name='guide')
    async def guide(ctx):
        """Affiche le guide complet du bot"""
        
        embed = embed_creator.create_guide_embed()
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
    
    @bot.command(name='clear')
    async def clear(ctx, nombre: int = 1):
        """Supprime des messages du salon"""
        try:
            deleted = await ctx.channel.purge(limit=nombre + 1)
            msg = await ctx.send(f"✅ {len(deleted) - 1} message(s) supprimé(s)")
            await asyncio.sleep(3)
            await msg.delete()
        except discord.Forbidden:
            await ctx.send("❌ Permissions insuffisantes !")
        except discord.HTTPException:
            await ctx.send("❌ Impossible de supprimer tous les messages")
    
    @bot.command(name='status')
    async def status(ctx):
        """Affiche le statut actuel de la partie"""
        
        embed = embed_creator.create_status_embed(game_session, formatters, bot)
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
    
    @bot.command(name='disconnect')
    async def disconnect(ctx):
        """Déconnecte le bot"""
        await ctx.send("👋 **WikiBot** se déconnecte...")
        await ctx.message.delete()
        await bot.close()
    
    @bot.command(name='leave')
    async def leave(ctx):
        """Permet à un joueur de quitter la partie classée en cours"""
        
        if not game_session.enabled:
            embed = embed_creator.create_error_embed(
                "Aucune partie classée n'est active."
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        player_name = ctx.author.name
        
        if player_name not in game_session.members:
            embed = embed_creator.create_error_embed(
                "Vous ne faites pas partie de la partie en cours."
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        game_session.members.remove(player_name)

        if game_session.winner and game_session.winner.name == player_name:
            game_session.winner = None
        
        await ctx.send(
            f"👋 **{ctx.author.display_name}** a quitté la partie classée.\n"
            f"Joueurs restants : {formatters.format_player_list(game_session.members) if game_session.members else '**Aucun**'}"
        )
        await ctx.message.delete()
        
        # Si plus personne dans la partie, la dissoudre
        if not game_session.members:
            await ctx.send("🔴 **Partie dissoute** - Aucun joueur restant.")
            game_session.reset()
    
    @bot.command(name='disband')
    async def disband(ctx):
        """Dissout la partie classée en cours"""
        
        if not game_session.enabled:
            embed = embed_creator.create_error_embed(
                "Aucune partie classée n'est active."
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        player_name = ctx.author.name
        
        if player_name not in game_session.members:
            embed = embed_creator.create_error_embed(
                "Vous ne faites pas partie de la partie en cours."
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        # Demander confirmation
        embed = embed_creator.create_warning_embed(
            "Dissoudre la partie",
            f"**{ctx.author.display_name}**, voulez-vous vraiment dissoudre la partie classée ?\n"
            f"Tous les joueurs seront retirés : {formatters.format_player_list(game_session.members)}"
        )
        confirm_msg = await ctx.send(embed=embed)
        await confirm_msg.add_reaction('✅')
        await confirm_msg.add_reaction('❌')
        
        def check(reaction, user):
            return (user == ctx.author and 
                   str(reaction.emoji) in ['✅', '❌'] and 
                   reaction.message.id == confirm_msg.id)
        
        try:
            reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            if str(reaction.emoji) == '❌':
                embed = embed_creator.create_error_embed("Dissolution annulée.")
                await confirm_msg.edit(embed=embed)
                await confirm_msg.delete(delay=5)
                await ctx.message.delete()
                return
            
            # Dissoudre la partie
            channel_name = "le salon"
            if game_session.channel_id:
                channel = bot.get_channel(game_session.channel_id)
                if channel:
                    channel_name = f"**{channel.name}**"
            
            await confirm_msg.delete()
            await ctx.send(
                f"💥 **Partie dissoute** par {ctx.author.mention}\n"
                f"La partie classée dans {channel_name} a été terminée."
            )
            await ctx.message.delete()
            
            game_session.reset()
            
        except asyncio.TimeoutError:
            embed = embed_creator.create_error_embed("⏱️ Temps écoulé - Dissolution annulée")
            await confirm_msg.edit(embed=embed)
            await confirm_msg.delete(delay=5)
            await ctx.message.delete()
    
    return sommaire, guide, clear, status, disconnect, leave, disband