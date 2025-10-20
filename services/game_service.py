#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Service de gestion de la logique de jeu
"""

from typing import Dict, Tuple


class GameService:
    """Service de gestion de la logique de jeu"""
    
    def __init__(self, player_service, stats_service):
        self.player_service = player_service
        self.stats_service = stats_service
    
    def register_win(self, winner_name: str, temps: float, clicks: int, 
                    articles: Tuple[str, str], session_members: list) -> Dict:
        """
        Enregistre une victoire et retourne les informations de récompense
        """
        # Calculs
        points = self.stats_service.calculate_points(temps, clicks)
        xp_gained = self.stats_service.calculate_xp_gain(temps, clicks, True)
        
        # Charger les données
        player_data = self.player_service.get_player(winner_name)
        old_level = player_data['level']
        
        # Mettre à jour les stats
        player_data['points'] += points
        player_data['parties_gagnees'] += 1
        player_data['clics_total'] += clicks
        player_data['moyenne_clics'] = self.stats_service.calculate_average(
            clicks, 
            player_data['parties_gagnees'], 
            player_data['moyenne_clics']
        )
        player_data['temps_total'] += temps
        player_data['temps_moyen'] = self.stats_service.calculate_average(
            temps,
            player_data['parties_gagnees'],
            player_data['temps_moyen']
        )
        
        # Records personnels
        records_beaten = []
        if temps < player_data.get('best_time', float('inf')):
            player_data['best_time'] = temps
            if player_data['parties_gagnees'] > 1:
                records_beaten.append('time')
        
        if clicks < player_data.get('best_clicks', float('inf')):
            player_data['best_clicks'] = clicks
            if player_data['parties_gagnees'] > 1:
                records_beaten.append('clicks')
        
        if points > player_data.get('best_score', 0):
            player_data['best_score'] = points
            if player_data['parties_gagnees'] > 1:
                records_beaten.append('score')
        
        # Win streak
        player_data['win_streak'] = player_data.get('win_streak', 0) + 1
        player_data['best_win_streak'] = max(
            player_data.get('best_win_streak', 0),
            player_data['win_streak']
        )
        
        # Ajouter les articles visités
        articles_visited = set(player_data.get('articles_visited', []))
        articles_visited.add(articles[0])
        articles_visited.add(articles[1])
        player_data['articles_visited'] = list(articles_visited)
        
        # Sauvegarder avant d'ajouter XP
        self.player_service.save_player(winner_name, player_data)
        
        # Ajouter XP gameplay et vérifier level up
        level_up, old_lvl, new_lvl = self.player_service.add_xp(winner_name, xp_gained)
        
        # Vérifier et débloquer les achievements
        new_achievements, achievement_xp = self.player_service.check_achievements(winner_name)
        
        # Réinitialiser win streak pour les autres joueurs
        self.player_service.reset_win_streaks_except(session_members, winner_name)
        
        # Mettre à jour les classements
        self.player_service.update_rankings()
        
        # Recharger les données finales
        player_data = self.player_service.get_player(winner_name)
        
        return {
            'points': points,
            'xp_gained': xp_gained,
            'achievement_xp': achievement_xp,
            'total_xp': xp_gained + achievement_xp,
            'level_up': level_up,
            'old_level': old_lvl,
            'new_level': new_lvl,
            'new_achievements': new_achievements,
            'records_beaten': records_beaten,
            'player_data': player_data
        }
