#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Repository pour la persistance des données joueurs
"""

import json
from pathlib import Path
from typing import Optional, List, Dict


class PlayerRepository:
    """Gestion de la persistance des données joueurs"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.data_dir.mkdir(exist_ok=True)
    
    def get_filepath(self, player_name: str) -> Path:
        """Retourne le chemin du fichier JSON du joueur"""
        return self.data_dir / f"{player_name}.json"
    
    def exists(self, player_name: str) -> bool:
        """Vérifie si un joueur existe"""
        return self.get_filepath(player_name).exists()
    
    def load(self, player_name: str) -> Optional[Dict]:
        """Charge les données d'un joueur"""
        filepath = self.get_filepath(player_name)
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    def save(self, player_name: str, data: Dict) -> None:
        """Sauvegarde les données d'un joueur"""
        filepath = self.get_filepath(player_name)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_all(self) -> List[Dict]:
        """Retourne tous les joueurs"""
        players = []
        for file in self.data_dir.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['name'] = file.stem
                players.append(data)
        return players
    
    def delete(self, player_name: str) -> bool:
        """Supprime un joueur"""
        filepath = self.get_filepath(player_name)
        if filepath.exists():
            filepath.unlink()
            return True
        return False