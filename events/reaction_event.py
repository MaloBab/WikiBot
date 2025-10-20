#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Gestion des réactions aux messages
"""

import discord


async def on_reaction_add_handler(reaction, user, bot, game_session, 
                                  player_service, way_command):
    """Gestion des réactions aux messages"""
    if user.bot:
        return
    
    channel = reaction.message.channel
    
    # 🔄 Régénérer le chemin
    if reaction.emoji == "🔄" and reaction.message.author == bot.user:
        try:
            await reaction.message.delete()
        except discord.NotFound:
            pass
        
        # Créer un fake context pour la commande
        class FakeContext:
            def __init__(self, channel, author):
                self.channel = channel
                self.author = author
                self.message = None
            
            async def send(self, content=None, **kwargs):
                return await self.channel.send(content, **kwargs)
        
        fake_ctx = FakeContext(channel, user)
        await way_command(fake_ctx)
        return
    
    # ✅ Démarrer la partie
    elif reaction.emoji == "✅" and reaction.message.author == bot.user:
        try:
            await reaction.message.clear_reactions()
            await reaction.message.add_reaction("🏁")
            await reaction.message.add_reaction("❌")
        except discord.NotFound:
            return
        
        game_session.chrono_msg = await channel.send(
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⏱️ **CHRONOMÈTRE LANCÉ !**\n"
            "Le temps vous est compté !\n"
            "━━━━━━━━━━━━━━━━━━━━━"
        )
        game_session.timer.start()
        
        # Incrémenter parties jouées et streak
        if game_session.enabled:
            player_service.increment_played_games(game_session.members)
    
    # ❌ Annuler la partie
    elif reaction.emoji == "❌" and reaction.message.author == bot.user:
        try:
            await reaction.message.clear_reactions()
        except discord.NotFound:
            pass
        
        await channel.send("━━━━━━━━━━━━━━━━━━━━━\n"
                          "🚫 **PARTIE ANNULÉE**\n"
                          "━━━━━━━━━━━━━━━━━━━━━")
        game_session.timer.reset()
        
        # Décrémenter parties jouées et streak
        if game_session.enabled:
            player_service.decrement_played_games(game_session.members)
        
        try:
            await reaction.message.delete()
            if game_session.chrono_msg:
                await game_session.chrono_msg.delete()
        except discord.NotFound:
            pass
    
    # 🏁 Terminer la partie
    elif reaction.emoji == "🏁" and reaction.message.author == bot.user:
        try:
            await reaction.message.clear_reactions()
        except discord.NotFound:
            pass
        
        game_session.timer.stop()
        game_session.winner = user
        
        if game_session.enabled:
            await channel.send(
                f"> 🎉 **Félicitations {user.mention} !**\n"
                f"> Vous avez relié **{game_session.parcours[0].title}** "
                f"à **{game_session.parcours[1].title}**\n"
                f"> ⏱️ Temps : **{game_session.timer.duration}s**\n\n"
                f"> 💾 Pour enregistrer votre score : `%win <nombre_de_clics>`"
            )
        else:
            await channel.send(
                f"> 🎉 **Bravo {user.mention} !**\n"
                f"> Temps : **{game_session.timer.duration}s**\n"
                f"> ⚠️ *Partie non classée - score non enregistrable*"
            )
