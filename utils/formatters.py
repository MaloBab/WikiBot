"""
Fonctions de formatage pour l'affichage
"""

from typing import List, Tuple


class Formatters:
    """Utilitaires de formatage"""
    
    @staticmethod
    def format_time(seconds: float) -> Tuple[int, int, int]:
        """Formate un temps en heures, minutes, secondes"""
        minutes, secs = divmod(float(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return int(hours), int(minutes), int(secs)
    
    @staticmethod
    def format_player_list(players: List[str]) -> str:
        """Formate une liste de joueurs pour l'affichage"""
        if not players:
            return ""
        if len(players) == 1:
            return f"**{players[0]}**"
        return ", ".join(f"**{p}**" for p in players[:-1]) + f" et **{players[-1]}**"
    
    @staticmethod
    def get_progress_bar(current: int, maximum: int, length: int = 10) -> str:
        """Génère une barre de progression"""
        filled = int((current / maximum) * length) if maximum > 0 else 0
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {current}/{maximum}"
    
    @staticmethod
    def get_rank_display(rank: int) -> str:
        """Formate l'affichage du classement avec emoji"""
        if rank == 1:
            return "🥇 1er"
        elif rank == 2:
            return "🥈 2ème"
        elif rank == 3:
            return "🥉 3ème"
        else:
            return f"{rank}ème"
    
    @staticmethod
    def get_medal_emoji(position: int) -> str:
        """Retourne l'emoji de médaille selon la position"""
        if position == 1:
            return "🥇"
        elif position == 2:
            return "🥈"
        elif position == 3:
            return "🥉"
        else:
            return f"{position}."
