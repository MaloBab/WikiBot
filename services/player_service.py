#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Service de gestion des joueurs
"""

from typing import Optional, List, Dict, Tuple
from datetime import datetime


class PlayerService:
    """Service de gestion des joueurs"""
    
    def __init__(self, repository, constants):
        self.repository = repository
        self.LEVEL_THRESHOLDS = constants['LEVEL_THRESHOLDS']
        self.RANKS = constants['RANKS']
        self.ACHIEVEMENTS = constants['ACHIEVEMENTS']
    
    def create_player(self, player_name: str) -> Dict:
        """Crée un nouveau joueur ou charge ses données"""
        if not self.repository.exists(player_name):
            from models.player import Player
            data = Player.create_default_data()
            self.repository.save(player_name, data)
            return data
        return self.repository.load(player_name)
    
    def get_player(self, player_name: str) -> Optional[Dict]:
        """Récupère un joueur"""
        return self.repository.load(player_name)
    
    def save_player(self, player_name: str, data: Dict) -> None:
        """Sauvegarde un joueur"""
        self.repository.save(player_name, data)
    
    def get_all_players(self, sort_by: str = 'points') -> List[Dict]:
        """Retourne tous les joueurs triés"""
        players = self.repository.get_all()
        
        if sort_by == 'level':
            return sorted(players, key=lambda x: x['level'], reverse=True)
        elif sort_by == 'xp':
            return sorted(players, key=lambda x: x['xp'], reverse=True)
        elif sort_by == 'winrate':
            for p in players:
                p['win_rate'] = (p['parties_gagnees'] / p['parties_jouees'] * 100) if p['parties_jouees'] > 0 else 0
            return sorted(players, key=lambda x: x['win_rate'], reverse=True)
        else:
            return sorted(players, key=lambda x: x['points'], reverse=True)
    
    def update_rankings(self) -> None:
        """Met à jour le classement de tous les joueurs"""
        players = self.get_all_players()
        for i, player in enumerate(players, 1):
            player_data = self.get_player(player['name'])
            if player_data:
                player_data['classement'] = i
                self.save_player(player['name'], player_data)
    
    def add_xp(self, player_name: str, xp_amount: int) -> Tuple[bool, int, int]:
        """
        Ajoute de l'XP à un joueur et gère les montées de niveau
        Retourne: (level_up, old_level, new_level)
        """
        player_data = self.get_player(player_name)
        if not player_data:
            return False, 0, 0
        
        old_level = player_data['level']
        player_data['xp'] += xp_amount
        
        # Vérifier les montées de niveau
        new_level = old_level
        for level, required_xp in sorted(self.LEVEL_THRESHOLDS.items()):
            if player_data['xp'] >= required_xp:
                new_level = level
        
        player_data['level'] = new_level
        self.save_player(player_name, player_data)
        
        return new_level > old_level, old_level, new_level
    
    def check_achievements(self, player_name: str) -> Tuple[List[Dict], int]:
        """
        Vérifie et débloque les achievements d'un joueur
        Retourne: (liste des nouveaux achievements, XP total gagné)
        """
        player_data = self.get_player(player_name)
        if not player_data:
            return [], 0
        
        unlocked = []
        current_achievements = player_data.get('achievements', [])
        total_xp_from_achievements = 0
        
        for achievement_id, achievement in self.ACHIEVEMENTS.items():
            if achievement_id not in current_achievements:
                if achievement['check'](player_data):
                    current_achievements.append(achievement_id)
                    unlocked.append(achievement)
                    total_xp_from_achievements += achievement['xp']
        
        player_data['achievements'] = current_achievements
        self.save_player(player_name, player_data)
        
        if total_xp_from_achievements > 0:
            self.add_xp(player_name, total_xp_from_achievements)
        
        return unlocked, total_xp_from_achievements
    
    def get_rank_info(self, level: int) -> Dict:
        """Retourne les informations du rang selon le niveau"""
        for level_range, rank_info in self.RANKS.items():
            if level in level_range:
                return rank_info
        return self.RANKS[range(1, 5)]
    
    def increment_played_games(self, player_names: List[str]) -> None:
        """Incrémente le compteur de parties jouées pour plusieurs joueurs"""
        for player_name in player_names:
            player_data = self.get_player(player_name)
            if player_data:
                player_data['parties_jouees'] += 1
                player_data['current_streak'] += 1
                player_data['last_played'] = datetime.now().isoformat()
                self.save_player(player_name, player_data)
    
    def decrement_played_games(self, player_names: List[str]) -> None:
        """Décrémente le compteur de parties jouées pour plusieurs joueurs"""
        for player_name in player_names:
            player_data = self.get_player(player_name)
            if player_data:
                player_data['parties_jouees'] = max(0, player_data['parties_jouees'] - 1)
                player_data['current_streak'] = max(0, player_data['current_streak'] - 1)
                self.save_player(player_name, player_data)
    
    def reset_win_streaks_except(self, player_names: List[str], exception: str) -> None:
        """Réinitialise les win streaks de tous les joueurs sauf un"""
        for player_name in player_names:
            if player_name != exception:
                player_data = self.get_player(player_name)
                if player_data:
                    player_data['win_streak'] = 0
                    self.save_player(player_name, player_data)
