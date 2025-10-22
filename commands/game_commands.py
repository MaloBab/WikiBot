#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Commandes de jeu
"""

import discord
import asyncio
from discord.ext import commands


def setup_game_commands(bot, game_session, player_service, game_service, 
                       wikipedia_service, embed_creator, formatters, validators):
    """Configure les commandes de jeu"""
    
    @bot.command(name='partie')
    async def partie(ctx):
        """Démarre une partie classée"""
        
        if not validators.is_in_voice_channel(ctx.author):
            embed = embed_creator.create_error_embed(
                "Vous devez être connecté à un salon vocal !"
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        try:
            channel = ctx.author.voice.channel
            human_members = validators.get_human_members(channel)
            
            if not human_members:
                embed = embed_creator.create_error_embed(
                    "Aucun joueur humain détecté dans le salon vocal."
                )
                await ctx.send(embed=embed, delete_after=10)
                await ctx.message.delete(delay=10)
                return
            
            # Si une partie est déjà active dans ce salon
            if game_session.enabled and game_session.channel_id == channel.id:
                embed = embed_creator.create_warning_embed(
                    "Partie déjà active",
                    f"Une partie classée est déjà en cours dans **{channel.name}**"
                )
                await ctx.send(embed=embed, delete_after=10)
                await ctx.message.delete(delay=10)
                return
            
            # Confirmation pour partie solo
            if len(human_members) < 2:
                embed = embed_creator.create_warning_embed(
                    "Partie solo",
                    f"Vous êtes seul dans **{channel.name}**.\nConfirmer ?"
                )
                warning_msg = await ctx.send(embed=embed)
                await warning_msg.add_reaction('✅')
                await warning_msg.add_reaction('❌')
                
                def check(reaction, user):
                    return (user == ctx.author and 
                           str(reaction.emoji) in ['✅', '❌'] and 
                           reaction.message.id == warning_msg.id)
                
                try:
                    reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                    if str(reaction.emoji) == '❌':
                        embed = embed_creator.create_error_embed("🚫 Annulé")
                        await warning_msg.edit(embed=embed)
                        await warning_msg.delete(delay=5)
                        await ctx.message.delete()
                        return
                    await warning_msg.delete()
                except asyncio.TimeoutError:
                    embed = embed_creator.create_error_embed("⏱️ Temps écoulé")
                    await warning_msg.edit(embed=embed)
                    await warning_msg.delete(delay=5)
                    await ctx.message.delete()
                    return
            
            # Initialiser la session
            from datetime import datetime
            game_session.members = [m.name for m in human_members]
            game_session.enabled = True
            game_session.channel_id = channel.id
            game_session.start_time = datetime.now()
            
            new_players = []
            
            for member_name in game_session.members:
                player_data = player_service.get_player(member_name)
                if not player_data:
                    player_service.create_player(member_name)
                    new_players.append(member_name)
            
            # Créer l'embed de partie
            embed = embed_creator.create_game_created_embed(
                channel.name, 
                game_session.members, 
                new_players, 
                ctx.author,
                formatters
            )
            
            await ctx.send(embed=embed)
            await ctx.message.delete()
            
        except Exception as e:
            embed = embed_creator.create_error_embed(f"```{str(e)}```")
            await ctx.send(embed=embed, delete_after=15)
            await ctx.message.delete()
    
    @bot.command(name='way')
    async def way(ctx):
        """Génère un parcours Wikipédia aléatoire"""
        
        if not game_session.enabled:
            annonce = await ctx.send(
                "⚠️ **Partie non classée**\n"
                "🔄 Génération du parcours..."
            )
        else:
            annonce = await ctx.send("🔄 Génération du parcours...")
        
        result = wikipedia_service.generate_path(max_attempts=10)
        
        if result is None:
            await annonce.delete()
            await ctx.send(
                "🔴 Impossible de générer un parcours après 10 tentatives."
            )
            return
        
        page1, page_target, attempt = result
        game_session.parcours = [page1, page_target]
        
        # Créer l'embed du parcours
        embed = embed_creator.create_path_embed(
            page1, 
            page_target, 
            game_session.enabled, 
            attempt
        )
        
        await annonce.delete()
        
        if ctx.message is not None:
            await ctx.message.delete()
        
        msg = await ctx.send(embed=embed)
        
        await msg.add_reaction("🔄")
        await msg.add_reaction("✅")
    
    @bot.command(name='win')
    async def win(ctx, clicks: int):
        """Enregistre la victoire avec calcul de points et XP"""
        
        if not game_session.enabled:
            await ctx.send("⚠️ Partie non classée - score non enregistrable !")
            await ctx.message.delete()
            return
        
        if ctx.author != game_session.winner:
            await ctx.send(f"❌ {ctx.author.mention} n'est pas le gagnant !")
            await ctx.message.delete()
            return
        
        try:
            winner_name = game_session.winner.name
            temps = float(game_session.timer.duration)
            
            # Enregistrer la victoire
            articles = (game_session.parcours[0].title, game_session.parcours[1].title)
            result = game_service.register_win(
                winner_name, 
                temps, 
                clicks, 
                articles, 
                game_session.members
            )
            
            result['temps'] = temps
            result['clicks'] = clicks
            
            # Obtenir les infos de rang
            rank_info = player_service.get_rank_info(result['player_data']['level'])
            
            # Créer l'embed de victoire
            embed = embed_creator.create_victory_embed(
                game_session.winner,
                result,
                rank_info,
                formatters
            )
            
            await ctx.send(embed=embed)
            await ctx.message.delete()
            
            game_session.reset_round()
            
        except ValueError:
            await ctx.send("❌ Le nombre de clics doit être un nombre entier !")
            await ctx.message.delete()
        except Exception as e:
            await ctx.send(f"🔴 Erreur : {str(e)}")
            await ctx.message.delete()
    
    return partie, way, win