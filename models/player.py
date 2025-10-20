#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Modèle Player pour représenter les données d'un joueur
"""

from datetime import datetime
from typing import Dict, List


class Player:
    """Représentation d'un joueur"""
    
    def __init__(self, data: Dict):
        self.points = data.get('points', 0)
        self.xp = data.get('xp', 0)
        self.level = data.get('level', 1)
        self.parties_jouees = data.get('parties_jouees', 0)
        self.parties_gagnees = data.get('parties_gagnees', 0)
        self.clics_total = data.get('clics_total', 0)
        self.moyenne_clics = data.get('moyenne_clics', 0.0)
        self.temps_total = data.get('temps_total', 0.0)
        self.temps_moyen = data.get('temps_moyen', 0.0)
        self.classement = data.get('classement', 0)
        
        # Records personnels
        self.best_time = data.get('best_time', float('inf'))
        self.best_clicks = data.get('best_clicks', float('inf'))
        self.best_score = data.get('best_score', 0)
        
        # Streaks
        self.current_streak = data.get('current_streak', 0)
        self.win_streak = data.get('win_streak', 0)
        self.best_win_streak = data.get('best_win_streak', 0)
        
        # Achievements
        self.achievements = data.get('achievements', [])
        self.articles_visited = data.get('articles_visited', [])
        
        # Historique
        self.last_played = data.get('last_played')
        self.created_at = data.get('created_at', datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convertit le joueur en dictionnaire"""
        return {
            'points': self.points,
            'xp': self.xp,
            'level': self.level,
            'parties_jouees': self.parties_jouees,
            'parties_gagnees': self.parties_gagnees,
            'clics_total': self.clics_total,
            'moyenne_clics': self.moyenne_clics,
            'temps_total': self.temps_total,
            'temps_moyen': self.temps_moyen,
            'classement': self.classement,
            'best_time': self.best_time,
            'best_clicks': self.best_clicks,
            'best_score': self.best_score,
            'current_streak': self.current_streak,
            'win_streak': self.win_streak,
            'best_win_streak': self.best_win_streak,
            'achievements': self.achievements,
            'articles_visited': self.articles_visited,
            'last_played': self.last_played,
            'created_at': self.created_at
        }
    
    @staticmethod
    def create_default_data() -> Dict:
        """Crée les données par défaut d'un nouveau joueur"""
        return {
            'points': 0,
            'xp': 0,
            'level': 1,
            'parties_jouees': 0,
            'parties_gagnees': 0,
            'clics_total': 0,
            'moyenne_clics': 0.0,
            'temps_total': 0.0,
            'temps_moyen': 0.0,
            'classement': 0,
            'best_time': float('inf'),
            'best_clicks': float('inf'),
            'best_score': 0,
            'current_streak': 0,
            'win_streak': 0,
            'best_win_streak': 0,
            'achievements': [],
            'articles_visited': [],
            'last_played': None,
            'created_at': datetime.now().isoformat()
        }
