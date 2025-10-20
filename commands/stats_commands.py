from discord.ext import commands


def setup_stats_commands(bot, player_service, embed_creator, formatters):
    """Configure les commandes de statistiques"""
    
    @bot.command(name='stats')
    async def stats(ctx, user: str = None):
        """Affiche les statistiques détaillées d'un joueur"""
        
        if user is None:
            user = ctx.author.name
        
        player_data = player_service.get_player(user)
        
        if not player_data:
            await ctx.send(f"❌ Le joueur **{user}** n'existe pas !")
            await ctx.message.delete()
            return
        
        # Obtenir le rang
        rank_info = player_service.get_rank_info(player_data['level'])
        
        # Créer l'embed
        embed = embed_creator.create_stats_embed(user, player_data, rank_info, formatters)
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
    
    @bot.command(name='achievements')
    async def achievements(ctx, user: str = None):
        """Affiche les achievements d'un joueur"""
        
        if user is None:
            user = ctx.author.name
        
        player_data = player_service.get_player(user)
        
        if not player_data:
            await ctx.send(f"❌ Le joueur **{user}** n'existe pas !")
            await ctx.message.delete()
            return
        
        rank_info = player_service.get_rank_info(player_data['level'])
        
        embed = embed_creator.create_achievements_embed(user, player_data, rank_info, formatters)
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
    
    @bot.command(name='scoreboard')
    async def scoreboard(ctx):
        """Affiche le classement des meilleurs joueurs"""
        
        players = player_service.get_all_players()
        
        if not players:
            await ctx.send("Aucun joueur enregistré !")
            await ctx.message.delete()
            return
        
        embed = embed_creator.create_scoreboard_embed(players, formatters)
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
    
    @bot.command(name='leaderboard')
    async def leaderboard(ctx, category: str = "points"):
        """Affiche différents classements (points, niveau, winrate, etc.)"""
        
        # Déterminer le tri
        if category.lower() in ["level", "niveau", "lvl"]:
            sort_by = "level"
        elif category.lower() in ["winrate", "wr", "victoires"]:
            sort_by = "winrate"
        elif category.lower() in ["xp", "experience"]:
            sort_by = "xp"
        else:
            sort_by = "points"
        
        players = player_service.get_all_players(sort_by=sort_by)
        
        if not players:
            await ctx.send("Aucun joueur enregistré !")
            await ctx.message.delete()
            return
        
        embed = embed_creator.create_leaderboard_embed(players, category, formatters)
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
    
    return stats, achievements, scoreboard, leaderboard
