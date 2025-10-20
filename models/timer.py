#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Modèle Timer pour le chronométrage des parties
"""

import time
from typing import Optional


class Timer:
    """Gestion du chronomètre de partie"""
    
    def __init__(self):
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: float = 0.0
    
    def start(self) -> None:
        """Démarre le chronomètre"""
        self.start_time = time.time()
    
    def stop(self) -> float:
        """Arrête le chronomètre et retourne la durée"""
        if self.start_time:
            self.end_time = time.time()
            self.duration = round(self.end_time - self.start_time, 2)
        return self.duration
    
    def reset(self) -> None:
        """Réinitialise le chronomètre"""
        self.start_time = None
        self.end_time = None
        self.duration = 0.0
    
    def get_elapsed(self) -> float:
        """Retourne le temps écoulé depuis le démarrage"""
        if self.start_time:
            return round(time.time() - self.start_time, 1)
        return 0.0