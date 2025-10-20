#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Modèle GameSession pour gérer l'état d'une partie
"""

import discord
from models.timer import Timer
from typing import Optional, List
from datetime import datetime


class GameSession:
    """Gestion d'une session de jeu"""
    
    def __init__(self):
        self.parcours: List = []
        self.enabled: bool = False
        self.members: List[str] = []
        self.timer: Timer = Timer()
        self.winner: Optional[discord.User] = None
        self.chrono_msg: Optional[discord.Message] = None
        self.channel_id: Optional[int] = None
        self.start_time: Optional[datetime] = None
    
    def reset(self) -> None:
        """Réinitialise la session"""
        self.parcours = []
        self.enabled = False
        self.members = []
        self.timer.reset()
        self.winner = None
        self.chrono_msg = None
        self.channel_id = None
        self.start_time = None
    
    def is_active(self) -> bool:
        """Vérifie si une partie est active"""
        return self.enabled
    
    def has_path(self) -> bool:
        """Vérifie si un parcours existe"""
        return len(self.parcours) == 2
    
    def reset_round(self) -> None:
        """Réinitialise uniquement le tour actuel (pas toute la session)"""
        self.parcours = []
        self.timer.reset()
        self.winner = None
        self.chrono_msg = None