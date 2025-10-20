#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Fonctions de calcul réutilisables
"""


class Calculators:
    """Utilitaires de calcul"""
    
    @staticmethod
    def calculate_percentage(part: float, total: float) -> float:
        """Calcule un pourcentage"""
        if total == 0:
            return 0.0
        return round((part / total) * 100, 1)
    
    @staticmethod
    def get_xp_for_next_level(current_level: int, thresholds: dict) -> int:
        """Retourne l'XP nécessaire pour le prochain niveau"""
        return thresholds.get(current_level + 1, thresholds.get(current_level, 0))
