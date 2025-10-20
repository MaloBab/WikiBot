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
    
    return sommaire, guide, clear, status, disconnect