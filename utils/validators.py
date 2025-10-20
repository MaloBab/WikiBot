#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Fonctions de validation
"""

import discord
from typing import Optional


class Validators:
    """Utilitaires de validation"""
    
    @staticmethod
    def is_in_voice_channel(member: discord.Member) -> bool:
        """Vérifie si un membre est dans un salon vocal"""
        return member.voice is not None
    
    @staticmethod
    def get_human_members(channel: discord.VoiceChannel) -> list:
        """Retourne les membres humains d'un salon vocal"""
        return [m for m in channel.members if not m.bot]
    
    @staticmethod
    def validate_clicks(clicks_str: str) -> Optional[int]:
        """Valide et convertit le nombre de clics"""
        try:
            clicks = int(clicks_str)
            return clicks if clicks > 0 else None
        except ValueError:
            return None