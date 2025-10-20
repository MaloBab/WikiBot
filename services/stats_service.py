#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Service de calcul des statistiques et récompenses
"""


class StatsService:
    """Service de calcul des statistiques"""
    
    def __init__(self, constants):
        self.BASE_POINTS = constants['BASE_POINTS']
        self.BASE_XP_WIN = constants['BASE_XP_WIN']
        self.BASE_XP_LOSE = constants['BASE_XP_LOSE']
        self.MIN_POINTS = constants['MIN_POINTS']
        self.TIME_BONUS_THRESHOLDS = constants['TIME_BONUS_THRESHOLDS']
        self.CLICK_BONUS_THRESHOLDS = constants['CLICK_BONUS_THRESHOLDS']
    
    def calculate_points(self, temps: float, clicks: int) -> int:
        """Calcule les points gagnés selon le temps et les clics"""
        time_factor = max(1, temps / 100)
        click_factor = max(1, clicks / 3)
        points = (self.BASE_POINTS / time_factor / click_factor) * 7
        return max(self.MIN_POINTS, round(points))
    
    def calculate_xp_gain(self, temps: float, clicks: int, win: bool) -> int:
        """Calcule l'XP gagnée selon la performance"""
        base_xp = self.BASE_XP_WIN if win else self.BASE_XP_LOSE
        
        # Bonus pour rapidité
        for threshold, bonus in sorted(self.TIME_BONUS_THRESHOLDS.items()):
            if temps < threshold:
                base_xp += bonus
                break
        
        # Bonus pour efficacité
        for threshold, bonus in sorted(self.CLICK_BONUS_THRESHOLDS.items()):
            if clicks <= threshold:
                base_xp += bonus
                break
        
        return base_xp
    
    def calculate_average(self, new_value: float, count: int, current_avg: float) -> float:
        """Calcule une nouvelle moyenne"""
        if count == 0:
            return new_value
        return round((current_avg * (count - 1) + new_value) / count, 2)
    
    def calculate_win_rate(self, parties_gagnees: int, parties_jouees: int) -> float:
        """Calcule le taux de victoire"""
        if parties_jouees == 0:
            return 0.0
        return round((parties_gagnees / parties_jouees) * 100, 1)