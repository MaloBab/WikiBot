#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Création des embeds Discord
"""

import discord
from discord import Embed
from datetime import datetime
from typing import Dict, List


class EmbedCreator:
    """Création des embeds pour le bot"""
    
    @staticmethod
    def create_error_embed(message: str) -> Embed:
        """Crée un embed d'erreur"""
        return Embed(
            title="❌ Erreur",
            description=message,
            color=0xFF0000
        )
    
    @staticmethod
    def create_warning_embed(title: str, message: str) -> Embed:
        """Crée un embed d'avertissement"""
        return Embed(
            title=f"⚠️ {title}",
            description=message,
            color=0xFFA500
        )
    
    @staticmethod
    def create_success_embed(message: str) -> Embed:
        """Crée un embed de succès"""
        return Embed(
            title="✅ Succès",
            description=message,
            color=0x00D166
        )
    
    @staticmethod
    def create_game_created_embed(channel_name: str, members: List[str], 
                                  new_players: List[str], author: discord.Member,
                                  formatter) -> Embed:
        """Crée l'embed de création de partie"""
        embed = Embed(
            title="🎮 PARTIE CLASSÉE CRÉÉE",
            description=f"Partie lancée dans **{channel_name}**",
            color=0x00D166,
            timestamp=datetime.now()
        )
        
        embed.add_field(
            name=f"👥 Joueurs ({len(members)})",
            value=formatter.format_player_list(members),
            inline=False
        )
        
        if new_players:
            embed.add_field(
                name="🆕 Nouveaux joueurs",
                value=formatter.format_player_list(new_players),
                inline=False
            )
        
        embed.add_field(
            name="📋 Instructions",
            value="• Utilisez `%way` pour générer un parcours\n"
                  "• Vos performances seront enregistrées\n"
                  "• La partie reste active tant que vous êtes dans le salon\n"
                  "• Utilisez `%leave` pour quitter la partie classée",
            inline=False
        )
        
        embed.set_footer(
            text=f"Lancé par {author.display_name}",
            icon_url=author.avatar.url if author.avatar else None
        )
        
        return embed
    
    @staticmethod
    def create_path_embed(page_start, page_end, is_ranked: bool, 
                         attempt: int = 1) -> Embed:
        """Crée l'embed du parcours Wikipedia"""
        embed = Embed(
            title="🗺️ NOUVEAU DÉFI WIKIPÉDIA",
            color=0x6366F1
        )
        
        embed.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/200px-Wikipedia-logo-v2.svg.png"
        )
        
        embed.add_field(
            name="🚀 DÉPART",
            value=f"**[{page_start.title}]({page_start.url})**",
            inline=True
        )
        
        embed.add_field(name="━━━", value="➡️", inline=True)
        
        embed.add_field(
            name="🏁 ARRIVÉE",
            value=f"**{page_end.title}**",
            inline=True
        )
        
        embed.add_field(
            name="📋 Objectif",
            value="Naviguez vers l'arrivée en utilisant uniquement les liens internes !",
            inline=False
        )
        
        if not is_ranked:
            embed.add_field(
                name="⚠️ Attention",
                value="*Partie non classée*",
                inline=False
            )
        
        footer_text = "🔄 Régénérer  |  ✅ Démarrer"
        if attempt > 1:
            footer_text += f"  |  Généré en {attempt} tentative(s)"
        
        embed.set_footer(text=footer_text)
        
        return embed
    
    @staticmethod
    def create_victory_embed(winner: discord.Member, result: Dict, 
                            rank_info: Dict, formatter) -> Embed:
        """Crée l'embed de victoire"""
        player_data = result['player_data']
        
        embed = Embed(
            title="🎉 VICTOIRE !",
            description=f"Bravo {winner.mention} !",
            color=rank_info['color'],
            timestamp=datetime.now()
        )
        
        # Performance
        embed.add_field(
            name="📊 Performance",
            value=f"⏱️ Temps : **{result.get('temps', 0)}s**\n"
                  f"🖱️ Clics : **{result.get('clicks', 0)}**\n"
                  f"💎 Points : **+{result['points']}** (Total: {player_data['points']})",
            inline=True
        )
        
        # Progression XP
        from config.constants import LEVEL_THRESHOLDS
        xp_for_next = LEVEL_THRESHOLDS.get(player_data['level'] + 1, player_data['xp'])
        xp_progress = formatter.get_progress_bar(player_data['xp'], xp_for_next, 12)
        
        xp_details = f"+{result['xp_gained']} gameplay"
        if result['achievement_xp'] > 0:
            xp_details += f" +{result['achievement_xp']} achievements"
        
        embed.add_field(
            name="⭐ Progression",
            value=f"🆙 XP : **+{result['total_xp']}** ({xp_details})\n"
                  f"{rank_info['emoji']} Niveau : **{player_data['level']}** ({rank_info['name']})\n"
                  f"`{xp_progress}`",
            inline=True
        )
        
        # Level up
        if result['level_up']:
            from services.player_service import PlayerService
            # Note: Dans le vrai code, on passerait le service en paramètre
            new_rank = rank_info  # Simplifié pour l'exemple
            embed.add_field(
                name="🎊 MONTÉE DE NIVEAU !",
                value=f"**Niveau {result['old_level']}** ➜ **Niveau {result['new_level']}**\n"
                      f"{new_rank['emoji']} Vous êtes maintenant **{new_rank['name']}** !",
                inline=False
            )
        
        # Nouveaux achievements
        if result['new_achievements']:
            achievements_text = "\n".join([
                f"{ach['name']} - *{ach['description']}* (+{ach['xp']} XP)"
                for ach in result['new_achievements']
            ])
            embed.add_field(
                name="🏆 NOUVEAUX SUCCÈS DÉBLOQUÉS !",
                value=achievements_text,
                inline=False
            )
        
        # Records battus
        if result['records_beaten']:
            records_map = {
                'time': "⚡ Nouveau record de temps !",
                'clicks': "🎯 Nouveau record de clics !",
                'score': "💎 Nouveau record de score !"
            }
            records_text = "\n".join([records_map[r] for r in result['records_beaten']])
            embed.add_field(
                name="🏅 Records",
                value=records_text,
                inline=False
            )
        
        embed.set_footer(
            text=f"Classement: #{player_data['classement']} • Win Streak: {player_data['win_streak']}",
            icon_url=winner.avatar.url if winner.avatar else None
        )
        
        return embed
    
    @staticmethod
    def create_stats_embed(player_name: str, player_data: Dict, 
                          rank_info: Dict, formatter) -> Embed:
        """Crée l'embed des statistiques d'un joueur"""
        from config.constants import LEVEL_THRESHOLDS
        
        # Formater les temps
        h_total, m_total, s_total = formatter.format_time(player_data['temps_total'])
        h_avg, m_avg, s_avg = formatter.format_time(player_data['temps_moyen'])
        
        # Classement avec emoji
        rank_display = formatter.get_rank_display(player_data['classement'])
        
        # Taux de victoire
        win_rate = 0
        if player_data['parties_jouees'] > 0:
            win_rate = round((player_data['parties_gagnees'] / player_data['parties_jouees']) * 100, 1)
        
        # XP Progress
        xp_for_next = LEVEL_THRESHOLDS.get(player_data['level'] + 1, player_data['xp'])
        xp_progress = formatter.get_progress_bar(player_data['xp'], xp_for_next, 15)
        
        # Créer l'embed
        embed = Embed(
            title=f"📊 STATISTIQUES DE {player_name.upper()}",
            color=rank_info['color'],
            timestamp=datetime.now()
        )
        
        # Section Niveau et Rang
        embed.add_field(
            name=f"{rank_info['emoji']} Niveau & Rang",
            value=f"**Niveau {player_data['level']}** - {rank_info['name']}\n"
                  f"`{xp_progress}`\n"
                  f"XP: {player_data['xp']}/{xp_for_next}",
            inline=False
        )
        
        # Section Performance
        embed.add_field(
            name="🎮 Performance",
            value=f"💎 **Points** : {player_data['points']}\n"
                  f"🏆 **Classement** : {rank_display}\n"
                  f"🎯 **Win Rate** : {win_rate}%",
            inline=True
        )
        
        # Section Parties
        embed.add_field(
            name="📈 Parties",
            value=f"🎲 **Jouées** : {player_data['parties_jouees']}\n"
                  f"✅ **Gagnées** : {player_data['parties_gagnees']}\n"
                  f"🔥 **Win Streak** : {player_data['win_streak']}",
            inline=True
        )
        
        # Section Records
        best_time_str = f"{player_data['best_time']:.2f}s" if player_data['best_time'] != float('inf') else "N/A"
        best_clicks_str = str(player_data['best_clicks']) if player_data['best_clicks'] != float('inf') else "N/A"
        
        embed.add_field(
            name="🏅 Records Personnels",
            value=f"⚡ **Meilleur temps** : {best_time_str}\n"
                  f"🎯 **Moins de clics** : {best_clicks_str}\n"
                  f"💎 **Meilleur score** : {player_data['best_score']}",
            inline=True
        )
        
        # Section Moyennes
        embed.add_field(
            name="📊 Moyennes",
            value=f"🖱️ **Clics** : {player_data['moyenne_clics']:.2f}\n"
                  f"⏱️ **Temps** : {m_avg}m {s_avg}s\n"
                  f"🗺️ **Articles visités** : {len(player_data.get('articles_visited', []))}",
            inline=True
        )
        
        # Section Temps total
        embed.add_field(
            name="⏳ Temps Total",
            value=f"**{h_total}h {m_total}m {s_total}s**",
            inline=True
        )
        
        # Section Achievements
        from config.constants import ACHIEVEMENTS
        achievements_count = len(player_data.get('achievements', []))
        total_achievements = len(ACHIEVEMENTS)
        achievements_progress = formatter.get_progress_bar(achievements_count, total_achievements, 10)
        
        embed.add_field(
            name=f"🏆 Succès ({achievements_count}/{total_achievements})",
            value=f"`{achievements_progress}`",
            inline=False
        )
        
        embed.set_footer(
            text=f"Streak record: {player_data.get('best_win_streak', 0)} • En jeu depuis: {player_data.get('created_at', 'N/A')[:10]}"
        )
        
        return embed
    
    @staticmethod
    def create_achievements_embed(player_name: str, player_data: Dict, 
                                 rank_info: Dict, formatter) -> Embed:
        """Crée l'embed des achievements"""
        from config.constants import ACHIEVEMENTS
        
        unlocked = player_data.get('achievements', [])
        
        embed = Embed(
            title=f"🏆 SUCCÈS DE {player_name.upper()}",
            description=f"Débloquer des succès vous rapporte de l'XP bonus !",
            color=rank_info['color']
        )
        
        # Achievements débloqués
        unlocked_text = []
        for ach_id in unlocked:
            if ach_id in ACHIEVEMENTS:
                ach = ACHIEVEMENTS[ach_id]
                unlocked_text.append(f"{ach['name']}\n*{ach['description']}* (+{ach['xp']} XP)")
        
        if unlocked_text:
            embed.add_field(
                name=f"✅ Débloqués ({len(unlocked)}/{len(ACHIEVEMENTS)})",
                value="\n\n".join(unlocked_text) if unlocked_text else "Aucun",
                inline=False
            )
        
        # Achievements verrouillés
        locked_text = []
        for ach_id, ach in ACHIEVEMENTS.items():
            if ach_id not in unlocked:
                locked_text.append(f"🔒 {ach['name']}\n*{ach['description']}* (+{ach['xp']} XP)")
        
        if locked_text:
            embed.add_field(
                name=f"🔒 À débloquer ({len(locked_text)})",
                value="\n\n".join(locked_text[:5]),
                inline=False
            )
        
        progress = formatter.get_progress_bar(len(unlocked), len(ACHIEVEMENTS), 15)
        embed.add_field(
            name="📊 Progression",
            value=f"`{progress}`",
            inline=False
        )
        
        return embed
    
    @staticmethod
    def create_scoreboard_embed(players: List[Dict], formatter) -> Embed:
        """Crée l'embed du classement général"""
        from services.player_service import PlayerService
        from config.constants import RANKS
        
        embed = Embed(
            title="🏆 CLASSEMENT GÉNÉRAL",
            description="Les meilleurs joueurs de Wikipédia Challenge",
            color=0xFFD700
        )
        
        for i, player in enumerate(players[:10], 1):
            # Obtenir le rang
            level = player['level']
            rank_info = None
            for level_range, info in RANKS.items():
                if level in level_range:
                    rank_info = info
                    break
            if not rank_info:
                rank_info = RANKS[range(1, 5)]
            
            medal = formatter.get_medal_emoji(i)
            
            win_rate = 0
            if player['parties_jouees'] > 0:
                win_rate = round((player['parties_gagnees'] / player['parties_jouees']) * 100, 1)
            
            embed.add_field(
                name=f"{medal} {player['name']}",
                value=f"{rank_info['emoji']} Niv. {player['level']} • **{player['points']} pts**\n"
                      f"🎯 {win_rate}% WR • 🏆 {player['parties_gagnees']} victoires",
                inline=False
            )
        
        return embed
    
    @staticmethod
    def create_leaderboard_embed(players: List[Dict], category: str, 
                                 formatter) -> Embed:
        """Crée l'embed d'un classement spécifique"""
        from config.constants import RANKS
        
        # Déterminer le titre
        if category in ["level", "niveau", "lvl"]:
            title = "🎖️ CLASSEMENT PAR NIVEAU"
        elif category in ["winrate", "wr", "victoires"]:
            title = "📈 CLASSEMENT PAR WINRATE"
        elif category in ["xp", "experience"]:
            title = "⭐ CLASSEMENT PAR XP"
        else:
            title = "💎 CLASSEMENT PAR POINTS"
        
        embed = Embed(title=title, color=0x6366F1)
        
        for i, player in enumerate(players[:10], 1):
            # Obtenir le rang
            level = player['level']
            rank_info = None
            for level_range, info in RANKS.items():
                if level in level_range:
                    rank_info = info
                    break
            if not rank_info:
                rank_info = RANKS[range(1, 5)]
            
            if category in ["winrate", "wr", "victoires"]:
                value = f"{rank_info['emoji']} Niv. {player['level']} • **{player.get('win_rate', 0):.1f}% WR**"
            elif category in ["level", "niveau", "lvl"]:
                value = f"**Niveau {player['level']}** {rank_info['emoji']}\n{player['xp']} XP • {player['points']} points"
            elif category in ["xp", "experience"]:
                value = f"{rank_info['emoji']} **{player['xp']} XP**\nNiveau {player['level']} • {player['points']} points"
            else:
                value = f"{rank_info['emoji']} Niv. {player['level']} • **{player['points']} pts**"
            
            medal = formatter.get_medal_emoji(i)
            
            embed.add_field(
                name=f"{medal} {player['name']}",
                value=value,
                inline=False
            )
        
        return embed
    
    @staticmethod
    def create_guide_embed() -> Embed:
        """Crée l'embed du guide"""
        embed = Embed(
            title="🌟 GUIDE WIKIPÉDIA CHALLENGE 🌟",
            description="Naviguez dans Wikipédia et progressez avec le système de niveaux !",
            color=0x6366F1
        )
        
        embed.set_thumbnail(
            url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/200px-Wikipedia-logo-v2.svg.png"
        )
        
        # Parties
        embed.add_field(
            name="🎮 JOUER",
            value="**%partie** - Créer une partie classée\n"
                  "**%way** - Générer un parcours\n"
                  "**%win <clics>** - Enregistrer votre victoire",
            inline=True
        )
        
        # Stats
        embed.add_field(
            name="📊 STATS",
            value="**%stats [joueur]** - Voir les statistiques\n"
                  "**%achievements** - Vos succès\n"
                  "**%scoreboard** - Top 10\n",
            inline=True
        )
        
        # Système de progression
        embed.add_field(
            name="⭐ SYSTÈME DE PROGRESSION",
            value="🥉 **Bronze** (Niv. 1-4)\n"
                  "🥈 **Argent** (Niv. 5-9)\n"
                  "🥇 **Or** (Niv. 10-14)\n"
                  "💍 **Platine** (Niv. 15-17)\n"
                  "💎 **Diamant** (Niv. 18-20)",
            inline=False
        )
        
        # Achievements
        embed.add_field(
            name="🏆 SUCCÈS À DÉBLOQUER",
            value="⚡ **Éclair** - Gagner en - 30s\n"
                  "🎯 **Minimaliste** - Gagner en -3 clics\n"
                  "🏃 **Marathon** - 10 parties d'affilée\n"
                  "🗺️ **Explorateur** - 100 articles visités\n"
                  "👑 **Perfectionniste** - 10 wins consécutives\n"
                  "*Et bien d'autres...*",
            inline=False
        )
        
        # Utilitaires
        embed.add_field(
            name="🔧 UTILITAIRES",
            value="**%sommaire <article>** - Résumé en MP\n"
                  "**%clear [n]** - Nettoyer le chat\n"
                  "**%disconnect** - Éteindre le bot",
            inline=False
        )
        
        embed.set_footer(text="🎉 Gagnez de l'XP, montez de niveau et déverrouillez des succès ! 🎉")
        
        return embed
    
    @staticmethod
    def create_status_embed(game_session, formatter, bot) -> Embed:
        """Crée l'embed du statut de la partie"""
        embed = Embed(
            title="📊 STATUT DE LA PARTIE",
            color=0x6366F1
        )
        
        if game_session.enabled:
            embed.add_field(
                name="🟢 Statut",
                value="**Partie classée ACTIVE**",
                inline=False
            )
            
            if game_session.channel_id:
                channel = bot.get_channel(game_session.channel_id)
                if channel:
                    embed.add_field(
                        name="🎤 Salon vocal",
                        value=f"**{channel.name}**",
                        inline=True
                    )
            
            embed.add_field(
                name=f"👥 Joueurs ({len(game_session.members)})",
                value=formatter.format_player_list(game_session.members) if game_session.members else "Aucun",
                inline=True
            )
            
            if game_session.parcours:
                embed.add_field(
                    name="🗺️ Parcours actif",
                    value=f"De **{game_session.parcours[0].title}** à **{game_session.parcours[1].title}**",
                    inline=False
                )
            
            if game_session.timer.start_time:
                elapsed = game_session.timer.get_elapsed()
                embed.add_field(
                    name="⏱️ Chrono",
                    value=f"**{elapsed:.1f}s** en cours",
                    inline=True
                )
        else:
            embed.add_field(
                name="🔴 Statut",
                value="**Aucune partie classée active**",
                inline=False
            )
        
        return embed
