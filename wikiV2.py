#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
WikiBot - Bot Discord pour le Wikipédia Challenge
Avec système de progression (niveaux, rangs, achievements)
"""

import discord
import wikipedia
from wikipedia.exceptions import DisambiguationError, PageError
import os
import random
import time
import json
import asyncio
from discord.ext import commands
from discord import Embed
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

# ==================== CONFIGURATION ====================


with open("TOKEN.dat", "r") as token_file:
    TOKEN = token_file.read().strip() 
DATA_DIR = Path("Joueurs")
DATA_DIR.mkdir(exist_ok=True)

# Paliers de niveaux (XP requis)
LEVEL_THRESHOLDS = {
    1: 0, 2: 100, 3: 250, 4: 450, 5: 700,
    6: 1000, 7: 1400, 8: 1850, 9: 2350, 10: 2900,
    11: 3500, 12: 4200, 13: 5000, 14: 5900, 15: 6900,
    16: 8000, 17: 9200, 18: 10500, 19: 12000, 20: 14000
}

# Rangs par niveau
RANKS = {
    range(1, 5): {"name": "Bronze", "emoji": "🥉", "color": 0xCD7F32},
    range(5, 10): {"name": "Argent", "emoji": "🥈", "color": 0xC0C0C0},
    range(10, 15): {"name": "Or", "emoji": "🥇", "color": 0xFFD700},
    range(15, 18): {"name": "Platine", "emoji": "💠", "color": 0xE5E4E2},
    range(18, 21): {"name": "Diamant", "emoji": "💎", "color": 0xB9F2FF},
}

# Définition des achievements
ACHIEVEMENTS = {
    "eclair": {
        "name": "⚡ Éclair",
        "description": "Gagner en moins de 30 secondes",
        "xp": 50,
        "check": lambda stats: stats.get("best_time", float('inf')) < 30
    },
    "minimaliste": {
        "name": "🎯 Minimaliste",
        "description": "Gagner en moins de 3 clics",
        "xp": 100,
        "check": lambda stats: stats.get("best_clicks", float('inf')) <= 3
    },
    "marathon": {
        "name": "🏃 Marathon",
        "description": "Jouer 10 parties d'affilée",
        "xp": 75,
        "check": lambda stats: stats.get("current_streak", 0) >= 10
    },
    "explorateur": {
        "name": "🗺️ Explorateur",
        "description": "Visiter 100 articles uniques",
        "xp": 150,
        "check": lambda stats: len(stats.get("articles_visited", [])) >= 100
    },
    "perfectionniste": {
        "name": "👑 Perfectionniste",
        "description": "10 victoires consécutives",
        "xp": 200,
        "check": lambda stats: stats.get("win_streak", 0) >= 10
    },
    "debutant": {
        "name": "🌱 Débutant",
        "description": "Jouer votre première partie",
        "xp": 10,
        "check": lambda stats: stats.get("parties_jouees", 0) >= 1
    },
    "veterane": {
        "name": "🎖️ Vétéran",
        "description": "Jouer 50 parties",
        "xp": 100,
        "check": lambda stats: stats.get("parties_jouees", 0) >= 50
    },
    "champion": {
        "name": "🏆 Champion",
        "description": "Gagner 25 parties",
        "xp": 150,
        "check": lambda stats: stats.get("parties_gagnees", 0) >= 25
    },
    "rapide": {
        "name": "💨 Rapide",
        "description": "Temps moyen inférieur à 60 secondes",
        "xp": 75,
        "check": lambda stats: stats.get("temps_moyen", float('inf')) < 60
    },
    "efficace": {
        "name": "🎲 Efficace",
        "description": "Moyenne de clics inférieure à 5",
        "xp": 75,
        "check": lambda stats: stats.get("moyenne_clics", float('inf')) < 5
    }
}

# ==================== CLASSES ====================

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


class PlayerData:
    """Gestion des données joueurs avec système de progression"""
    
    @staticmethod
    def get_filepath(player_name: str) -> Path:
        """Retourne le chemin du fichier JSON du joueur"""
        return DATA_DIR / f"{player_name}.json"
    
    @staticmethod
    def create_default_data() -> Dict:
        """Crée les données par défaut d'un nouveau joueur"""
        return {
            # Stats de base
            "points": 0,
            "xp": 0,
            "level": 1,
            "parties_jouees": 0,
            "parties_gagnees": 0,
            "clics_total": 0,
            "moyenne_clics": 0.0,
            "temps_total": 0.0,
            "temps_moyen": 0.0,
            "classement": 0,
            
            # Records personnels
            "best_time": float('inf'),
            "best_clicks": float('inf'),
            "best_score": 0,
            
            # Streaks
            "current_streak": 0,
            "win_streak": 0,
            "best_win_streak": 0,
            
            # Achievements
            "achievements": [],
            "articles_visited": [],
            
            # Historique
            "last_played": None,
            "created_at": datetime.now().isoformat()
        }
    
    @staticmethod
    def create_player(player_name: str) -> Dict:
        """Crée un nouveau joueur ou charge ses données"""
        filepath = PlayerData.get_filepath(player_name)
        if not filepath.exists():
            data = PlayerData.create_default_data()
            PlayerData.save_player(player_name, data)
            return data
        return PlayerData.load_player(player_name)
    
    @staticmethod
    def load_player(player_name: str) -> Optional[Dict]:
        """Charge les données d'un joueur"""
        filepath = PlayerData.get_filepath(player_name)
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None
    
    @staticmethod
    def save_player(player_name: str, data: Dict) -> None:
        """Sauvegarde les données d'un joueur"""
        filepath = PlayerData.get_filepath(player_name)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def get_all_players() -> List[Dict]:
        """Retourne tous les joueurs triés par points"""
        players = []
        for file in DATA_DIR.glob("*.json"):
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                data['name'] = file.stem
                players.append(data)
        return sorted(players, key=lambda x: x['points'], reverse=True)
    
    @staticmethod
    def update_rankings() -> None:
        """Met à jour le classement de tous les joueurs"""
        players = PlayerData.get_all_players()
        for i, player in enumerate(players, 1):
            player_data = PlayerData.load_player(player['name'])
            if player_data:
                player_data['classement'] = i
                PlayerData.save_player(player['name'], player_data)
    
    @staticmethod
    def add_xp(player_name: str, xp_amount: int) -> Tuple[bool, int, int]:
        """
        Ajoute de l'XP à un joueur et gère les montées de niveau
        Retourne: (level_up, old_level, new_level)
        """
        player_data = PlayerData.load_player(player_name)
        if not player_data:
            return False, 0, 0
        
        old_level = player_data['level']
        player_data['xp'] += xp_amount
        
        # Vérifier les montées de niveau
        new_level = old_level
        for level, required_xp in sorted(LEVEL_THRESHOLDS.items()):
            if player_data['xp'] >= required_xp:
                new_level = level
        
        player_data['level'] = new_level
        PlayerData.save_player(player_name, player_data)
        
        return new_level > old_level, old_level, new_level
    

    @staticmethod
    def check_achievements(player_name: str) -> Tuple[List[Dict], int]:
        """
        Vérifie et débloque les achievements d'un joueur
        Retourne: (liste des nouveaux achievements, XP total gagné)
        """
        player_data = PlayerData.load_player(player_name)
        if not player_data:
            return [], 0
        
        unlocked = []
        current_achievements = player_data.get('achievements', [])
        total_xp_from_achievements = 0
        
        for achievement_id, achievement in ACHIEVEMENTS.items():
            # Si pas encore débloqué et condition remplie
            if achievement_id not in current_achievements:
                if achievement['check'](player_data):
                    current_achievements.append(achievement_id)
                    unlocked.append(achievement)
                    # Accumuler l'XP du achievement
                    xp_amount = achievement['xp']
                    total_xp_from_achievements += xp_amount
        
        player_data['achievements'] = current_achievements
        PlayerData.save_player(player_name, player_data)
        
        # Ajouter TOUT l'XP des achievements en une seule fois
        if total_xp_from_achievements > 0:
            PlayerData.add_xp(player_name, total_xp_from_achievements)
        
        return unlocked, total_xp_from_achievements
    
    @staticmethod
    def get_rank_info(level: int) -> Dict:
        """Retourne les informations du rang selon le niveau"""
        for level_range, rank_info in RANKS.items():
            if level in level_range:
                return rank_info
        return RANKS[range(1, 5)]  # Bronze par défaut


# ==================== FONCTIONS UTILITAIRES ====================

def calculate_points(temps: float, clicks: int) -> int:
    """Calcule les points gagnés selon le temps et les clics"""
    base_points = 300
    time_factor = max(1, temps / 100)
    click_factor = max(1, clicks / 3)
    points = (base_points / time_factor / click_factor) * 7
    return max(10, round(points))  # Minimum 10 points

def calculate_xp_gain(temps: float, clicks: int, win: bool) -> int:
    """Calcule l'XP gagnée selon la performance"""
    base_xp = 20 if win else 5
    
    # Bonus pour rapidité
    if temps < 30:
        base_xp += 15
    elif temps < 60:
        base_xp += 10
    elif temps < 120:
        base_xp += 5
    
    # Bonus pour efficacité
    if clicks <= 3:
        base_xp += 20
    elif clicks <= 5:
        base_xp += 10
    elif clicks <= 10:
        base_xp += 5
    
    return base_xp

def calculate_average(new_value: float, count: int, current_avg: float) -> float:
    """Calcule une nouvelle moyenne"""
    if count == 0:
        return new_value
    return round((current_avg * (count - 1) + new_value) / count, 2)

def format_time(seconds: float) -> Tuple[int, int, int]:
    """Formate un temps en heures, minutes, secondes"""
    minutes, secs = divmod(float(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    return int(hours), int(minutes), int(secs)

def format_player_list(players: List[str]) -> str:
    """Formate une liste de joueurs pour l'affichage"""
    if not players:
        return ""
    if len(players) == 1:
        return f"**{players[0]}**"
    return ", ".join(f"**{p}**" for p in players[:-1]) + f" et **{players[-1]}**"

def get_progress_bar(current: int, maximum: int, length: int = 10) -> str:
    """Génère une barre de progression"""
    filled = int((current / maximum) * length) if maximum > 0 else 0
    bar = "█" * filled + "░" * (length - filled)
    return f"[{bar}] {current}/{maximum}"


# ==================== BOT SETUP ====================

intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.reactions = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(
    command_prefix='%',
    description="Wikipédia Challenge Manager avec système de progression",
    intents=intents,
    help_command=None
)

game_session = GameSession()


# ==================== EVENTS ====================

@bot.event
async def on_ready():
    """Initialisation du bot"""
    wikipedia.set_lang("fr")
    await bot.change_presence(activity=discord.Game('%guide'))
    print('━━━━━━━━━━━━━━━━━━━━━━')
    print('WikiBot est en ligne !')
    print(f'User: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('━━━━━━━━━━━━━━━━━━━━━━')



@bot.event
async def on_reaction_add(reaction, user):
    """Gestion des réactions aux messages"""
    if user.bot:
        return
    
    channel = reaction.message.channel
    
    # 🔄 Régénérer le chemin
    if reaction.emoji == "🔄" and reaction.message.author == bot.user:
        try:
            await reaction.message.delete()
        except discord.NotFound:
            pass
        
        # Créer un fake context pour la commande
        class FakeContext:
            def __init__(self, channel, author):
                self.channel = channel
                self.author = author
                self.message = None
            
            async def send(self, content=None, **kwargs):
                return await self.channel.send(content, **kwargs)
        
        fake_ctx = FakeContext(channel, user)
        await way(fake_ctx)
        return
    
    # ✅ Démarrer la partie
    elif reaction.emoji == "✅" and reaction.message.author == bot.user:
        try:
            await reaction.message.clear_reactions()
            await reaction.message.add_reaction("🏁")
            await reaction.message.add_reaction("❌")
        except discord.NotFound:
            return
        
        game_session.chrono_msg = await channel.send(
            "━━━━━━━━━━━━━━━━━━━━━━\n"
            "⏱️ **CHRONOMÈTRE LANCÉ !**\n"
            "Le temps vous est compté !\n"
            "━━━━━━━━━━━━━━━━━━━━━━"
        )
        game_session.timer.start()
        
        # Incrémenter parties jouées et streak
        if game_session.enabled:
            for member_name in game_session.members:
                player_data = PlayerData.load_player(member_name)
                if player_data:
                    player_data['parties_jouees'] += 1
                    player_data['current_streak'] += 1
                    player_data['last_played'] = datetime.now().isoformat()
                    PlayerData.save_player(member_name, player_data)
    
    # ❌ Annuler la partie
    elif reaction.emoji == "❌" and reaction.message.author == bot.user:
        try:
            await reaction.message.clear_reactions()
        except discord.NotFound:
            pass
        
        await channel.send("━━━━━━━━━━━━━━━━━━━━━━\n"
                          "🚫 **PARTIE ANNULÉE**\n"
                          "━━━━━━━━━━━━━━━━━━━━━━")
        game_session.timer.reset()
        
        # Décrémenter parties jouées et streak
        if game_session.enabled:
            for member_name in game_session.members:
                player_data = PlayerData.load_player(member_name)
                if player_data:
                    player_data['parties_jouees'] = max(0, player_data['parties_jouees'] - 1)
                    player_data['current_streak'] = max(0, player_data['current_streak'] - 1)
                    PlayerData.save_player(member_name, player_data)
        
        try:
            await reaction.message.delete()
            if game_session.chrono_msg:
                await game_session.chrono_msg.delete()
        except discord.NotFound:
            pass
    
    # 🏁 Terminer la partie
    elif reaction.emoji == "🏁" and reaction.message.author == bot.user:
        try:
            await reaction.message.clear_reactions()
        except discord.NotFound:
            pass
        
        game_session.timer.stop()
        game_session.winner = user
        
        if game_session.enabled:
            await channel.send(
                f"> 🎉 **Félicitations {user.mention} !**\n"
                f"> Vous avez relié **{game_session.parcours[0].title}** "
                f"à **{game_session.parcours[1].title}**\n"
                f"> ⏱️ Temps : **{game_session.timer.duration}s**\n\n"
                f"> 💾 Pour enregistrer votre score : `%win <nombre_de_clics>`"
            )
        else:
            await channel.send(
                f"> 🎉 **Bravo {user.mention} !**\n"
                f"> Temps : **{game_session.timer.duration}s**\n"
                f"> ⚠️ *Partie non classée - score non enregistrable*"
            )
            
            
@bot.event
async def on_voice_state_update(member, before, after):
    """Détecte quand un joueur quitte le salon vocal"""
    if member.bot:
        return
    
    # Si le membre quitte le salon vocal
    if before.channel and not after.channel:
        if member.name in game_session.members:
            # Retirer le membre de la session
            game_session.members.remove(member.name)
            
            # Si c'était le gagnant, réinitialiser
            if game_session.winner and game_session.winner.name == member.name:
                game_session.winner = None
            
            # Si le salon vocal est vide, réinitialiser la session
            if game_session.channel_id:
                try:
                    channel = bot.get_channel(game_session.channel_id)
                    human_members = [m for m in channel.members if not m.bot]
                    if not human_members:
                        game_session.reset()
                except:
                    pass

            
# ==================== COMMANDES - PARTIE ====================

@bot.command(name='partie')
async def partie(ctx):
    """Démarre une partie classée"""
    
    if not ctx.author.voice:
        embed = Embed(
            title="❌ Erreur",
            description="Vous devez être connecté à un salon vocal !",
            color=0xFF0000
        )
        await ctx.send(embed=embed, delete_after=10)
        await ctx.message.delete(delay=10)
        return
    
    try:
        channel = ctx.author.voice.channel
        human_members = [m for m in channel.members if not m.bot]
        
        if not human_members:
            embed = Embed(
                title="❌ Aucun joueur",
                description="Aucun joueur humain détecté dans le salon vocal.",
                color=0xFF0000
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        # Si une partie est déjà active dans ce salon
        if game_session.enabled and game_session.channel_id == channel.id:
            embed = Embed(
                title="⚠️ Partie déjà active",
                description=f"Une partie classée est déjà en cours dans **{channel.name}**",
                color=0xFFA500
            )
            await ctx.send(embed=embed, delete_after=10)
            await ctx.message.delete(delay=10)
            return
        
        # Confirmation pour partie solo
        if len(human_members) < 2:
            embed = Embed(
                title="⚠️ Partie solo",
                description=f"Vous êtes seul dans **{channel.name}**.\nConfirmer ?",
                color=0xFFA500
            )
            warning_msg = await ctx.send(embed=embed)
            await warning_msg.add_reaction('✅')
            await warning_msg.add_reaction('❌')
            
            def check(reaction, user):
                return (user == ctx.author and 
                       str(reaction.emoji) in ['✅', '❌'] and 
                       reaction.message.id == warning_msg.id)
            
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                if str(reaction.emoji) == '❌':
                    embed = Embed(title="🚫 Annulé", color=0x808080)
                    await warning_msg.edit(embed=embed)
                    await warning_msg.delete(delay=5)
                    await ctx.message.delete()
                    return
                await warning_msg.delete()
            except asyncio.TimeoutError:
                embed = Embed(title="⏱️ Temps écoulé", color=0x808080)
                await warning_msg.edit(embed=embed)
                await warning_msg.delete(delay=5)
                await ctx.message.delete()
                return
        
        # Initialiser la session
        game_session.members = [m.name for m in human_members]
        game_session.enabled = True
        game_session.channel_id = channel.id
        game_session.start_time = datetime.now()
        
        new_players = []
        
        for member_name in game_session.members:
            player_data = PlayerData.load_player(member_name)
            if not player_data:
                PlayerData.create_player(member_name)
                new_players.append(member_name)
        
        # Créer l'embed de partie
        embed = Embed(
            title="🎮 PARTIE CLASSÉE CRÉÉE",
            description=f"Partie lancée dans **{channel.name}**",
            color=0x00D166,
            timestamp=ctx.message.created_at
        )
        
        embed.add_field(
            name=f"👥 Joueurs ({len(game_session.members)})",
            value=format_player_list(game_session.members),
            inline=False
        )
        
        if new_players:
            embed.add_field(
                name="🆕 Nouveaux joueurs",
                value=format_player_list(new_players),
                inline=False
            )
        
        embed.add_field(
            name="📋 Instructions",
            value="• Utilisez `%way` pour générer un parcours\n"
                  "• Vos performances seront enregistrées\n"
                  "• La partie reste active tant que vous êtes dans le salon\n"
                  "• Utilisez `%leave` pour quitter la partie classée",
            inline=False
        )
        
        embed.set_footer(
            text=f"Lancé par {ctx.author.display_name}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
        
    except Exception as e:
        embed = Embed(
            title="❌ Erreur",
            description=f"```{str(e)}```",
            color=0xFF0000
        )
        await ctx.send(embed=embed, delete_after=15)
        await ctx.message.delete()


@bot.command(name='way')
async def way(ctx):
    """Génère un parcours Wikipédia aléatoire"""
    
    if not game_session.enabled:
        annonce = await ctx.send(
            "⚠️ **Partie non classée**\n"
            "🔄 Génération du parcours..."
        )
    else:
        annonce = await ctx.send("🔄 Génération du parcours...")
    
    max_attempts = 10
    attempt = 0
    
    while attempt < max_attempts:
        try:
            attempt += 1
            
            # Générer articles aléatoires
            pages = wikipedia.random(pages=10)
            art1 = random.choice(pages)
            art2 = random.choice(pages)
            
            # Article de départ
            try:
                page1 = wikipedia.page(wikipedia.search(art1)[0])
            except DisambiguationError as e:
                page1 = wikipedia.page(e.options[0])
            
            # Article d'arrivée (via un lien)
            try:
                page2 = wikipedia.page(art2)
            except DisambiguationError as e:
                page2 = wikipedia.page(e.options[0])
            
            if page2.links:
                target = random.choice(page2.links)
                target_search = wikipedia.search(target)
                if target_search:
                    target_final = random.choice(target_search)
                    try:
                        page_target = wikipedia.page(target_final)
                    except DisambiguationError as e:
                        page_target = wikipedia.page(e.options[0])
                else:
                    page_target = page2
            else:
                page_target = page2
            
            game_session.parcours = [page1, page_target]
            break
            
        except (PageError):
            if attempt < max_attempts:
                await annonce.edit(content=f"🔄 Tentative {attempt}/{max_attempts}...")
                await asyncio.sleep(0.2)
                continue
            else:
                await annonce.delete()
                await ctx.send(
                    f"🔴 Impossible de générer un parcours après {max_attempts} tentatives."
                )
                return
    
    # Créer l'embed du parcours
    embed = Embed(
        title="🗺️ NOUVEAU DÉFI WIKIPÉDIA",
        color=0x6366F1
    )
    
    embed.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/200px-Wikipedia-logo-v2.svg.png"
    )
    
    embed.add_field(
        name="🚀 DÉPART",
        value=f"**[{page1.title}]({page1.url})**",
        inline=True
    )
    
    embed.add_field(name="━━━━", value="➡️", inline=True)
    
    embed.add_field(
        name="🏁 ARRIVÉE",
        value=f"**{page_target.title}**",
        inline=True
    )
    
    embed.add_field(
        name="📋 Objectif",
        value="Naviguez vers l'arrivée en utilisant uniquement les liens internes !",
        inline=False
    )
    
    if not game_session.enabled:
        embed.add_field(
            name="⚠️ Attention",
            value="*Partie non classée*",
            inline=False
        )
    
    footer_text = "🔄 Régénérer  |  ✅ Démarrer"
    if attempt > 1:
        footer_text += f"  |  Généré en {attempt} tentative(s)"
    
    embed.set_footer(text=footer_text)
    
    await annonce.delete()
    
    if ctx.message is not None:
        await ctx.message.delete()
    
    msg = await ctx.send(embed=embed)
    
    await msg.add_reaction("🔄")
    await msg.add_reaction("✅")

@bot.command(name='win')
async def win(ctx, clicks: int):
    """Enregistre la victoire avec calcul de points et XP"""
    
    if not game_session.enabled:
        await ctx.send("⚠️ Partie non classée - score non enregistrable !")
        await ctx.message.delete()
        return
    
    if ctx.author != game_session.winner:
        await ctx.send(f"❌ {ctx.author.mention} n'est pas le gagnant !")
        await ctx.message.delete()
        return
    
    try:
        winner_name = game_session.winner.name
        temps = float(game_session.timer.duration)
        
        # Calculs
        points = calculate_points(temps, clicks)
        xp_gained = calculate_xp_gain(temps, clicks, True)
        
        # Charger les données
        player_data = PlayerData.load_player(winner_name)
        old_level = player_data['level']
        
        # Mettre à jour les stats
        player_data['points'] += points
        player_data['parties_gagnees'] += 1
        player_data['clics_total'] += clicks
        player_data['moyenne_clics'] = calculate_average(
            clicks, 
            player_data['parties_gagnees'], 
            player_data['moyenne_clics']
        )
        player_data['temps_total'] += temps
        player_data['temps_moyen'] = calculate_average(
            temps,
            player_data['parties_gagnees'],
            player_data['temps_moyen']
        )
        
        # Records personnels
        player_data['best_time'] = min(player_data.get('best_time', float('inf')), temps)
        player_data['best_clicks'] = min(player_data.get('best_clicks', float('inf')), clicks)
        player_data['best_score'] = max(player_data.get('best_score', 0), points)
        
        # Win streak
        player_data['win_streak'] = player_data.get('win_streak', 0) + 1
        player_data['best_win_streak'] = max(
            player_data.get('best_win_streak', 0),
            player_data['win_streak']
        )
        
        # Ajouter les articles visités
        articles_visited = set(player_data.get('articles_visited', []))
        articles_visited.add(game_session.parcours[0].title)
        articles_visited.add(game_session.parcours[1].title)
        player_data['articles_visited'] = list(articles_visited)
        
        # Sauvegarder avant d'ajouter XP
        PlayerData.save_player(winner_name, player_data)
        
        # Ajouter XP gameplay et vérifier level up
        level_up, old_lvl, new_lvl = PlayerData.add_xp(winner_name, xp_gained)
        
        # Vérifier et débloquer les achievements
        new_achievements, achievement_xp = PlayerData.check_achievements(winner_name)
        
        # XP total
        total_xp = xp_gained + achievement_xp
        
        # Réinitialiser win streak pour les autres joueurs
        for member_name in game_session.members:
            if member_name != winner_name:
                data = PlayerData.load_player(member_name)
                if data:
                    data['win_streak'] = 0
                    PlayerData.save_player(member_name, data)
        
        # Mettre à jour les classements
        PlayerData.update_rankings()
        
        # Recharger les données finales
        player_data = PlayerData.load_player(winner_name)
        rank_info = PlayerData.get_rank_info(player_data['level'])
        
        # Créer l'embed de victoire
        embed = Embed(
            title="🎉 VICTOIRE !",
            description=f"Bravo {game_session.winner.mention} !",
            color=rank_info['color'],
            timestamp=ctx.message.created_at
        )
        
        # Performance
        embed.add_field(
            name="📊 Performance",
            value=f"⏱️ Temps : **{temps}s**\n"
                  f"🖱️ Clics : **{clicks}**\n"
                  f"💎 Points : **+{points}** (Total: {player_data['points']})",
            inline=True
        )
        
        # Progression XP
        xp_for_next = LEVEL_THRESHOLDS.get(player_data['level'] + 1, player_data['xp'])
        xp_progress = get_progress_bar(player_data['xp'], xp_for_next, 12)
        
        xp_details = f"+{xp_gained} gameplay"
        if achievement_xp > 0:
            xp_details += f" +{achievement_xp} achievements"
        
        embed.add_field(
            name="⭐ Progression",
            value=f"🆙 XP : **+{total_xp}** ({xp_details})\n"
                  f"{rank_info['emoji']} Niveau : **{player_data['level']}** ({rank_info['name']})\n"
                  f"`{xp_progress}`",
            inline=True
        )
        
        # Level up
        if level_up:
            new_rank = PlayerData.get_rank_info(new_lvl)
            embed.add_field(
                name="🎊 MONTÉE DE NIVEAU !",
                value=f"**Niveau {old_lvl}** ➜ **Niveau {new_lvl}**\n"
                      f"{new_rank['emoji']} Vous êtes maintenant **{new_rank['name']}** !",
                inline=False
            )
        
        # Nouveaux achievements
        if new_achievements:
            achievements_text = "\n".join([
                f"{ach['name']} - *{ach['description']}* (+{ach['xp']} XP)"
                for ach in new_achievements
            ])
            embed.add_field(
                name="🏆 NOUVEAUX SUCCÈS DÉBLOQUÉS !",
                value=achievements_text,
                inline=False
            )
        
        # Records battus
        records = []
        if temps == player_data['best_time'] and player_data['parties_gagnees'] > 1:
            records.append("⚡ Nouveau record de temps !")
        if clicks == player_data['best_clicks'] and player_data['parties_gagnees'] > 1:
            records.append("🎯 Nouveau record de clics !")
        if points == player_data['best_score'] and player_data['parties_gagnees'] > 1:
            records.append("💎 Nouveau record de score !")
        
        if records:
            embed.add_field(
                name="🏅 Records",
                value="\n".join(records),
                inline=False
            )
        
        embed.set_footer(
            text=f"Classement: #{player_data['classement']} • Win Streak: {player_data['win_streak']}",
            icon_url=ctx.author.avatar.url if ctx.author.avatar else None
        )
        
        await ctx.send(embed=embed)
        await ctx.message.delete()
        
        # Réinitialiser SEULEMENT le chrono et le parcours, pas toute la session
        game_session.parcours = []
        game_session.timer.reset()
        game_session.winner = None
        game_session.chrono_msg = None
        
    except ValueError:
        await ctx.send("❌ Le nombre de clics doit être un nombre entier !")
        await ctx.message.delete()
    except Exception as e:
        await ctx.send(f"🔴 Erreur : {str(e)}")
        await ctx.message.delete()
        
# ==================== COMMANDES - STATS ====================

@bot.command(name='stats')
async def stats(ctx, user: str = None):
    """Affiche les statistiques détaillées d'un joueur"""
    
    if user is None:
        user = ctx.author.name
    
    player_data = PlayerData.load_player(user)
    
    if not player_data:
        await ctx.send(f"❌ Le joueur **{user}** n'existe pas !")
        await ctx.message.delete()
        return
    
    # Obtenir le rang
    rank_info = PlayerData.get_rank_info(player_data['level'])
    
    # Formater les temps
    h_total, m_total, s_total = format_time(player_data['temps_total'])
    h_avg, m_avg, s_avg = format_time(player_data['temps_moyen'])
    
    # Classement avec emoji
    rank_display = f"{player_data['classement']}ème"
    if player_data['classement'] == 1:
        rank_display = "🥇 1er"
    elif player_data['classement'] == 2:
        rank_display = "🥈 2ème"
    elif player_data['classement'] == 3:
        rank_display = "🥉 3ème"
    
    # Taux de victoire
    win_rate = 0
    if player_data['parties_jouees'] > 0:
        win_rate = round((player_data['parties_gagnees'] / player_data['parties_jouees']) * 100, 1)
    
    # XP Progress
    xp_for_next = LEVEL_THRESHOLDS.get(player_data['level'] + 1, player_data['xp'])
    xp_progress = get_progress_bar(player_data['xp'], xp_for_next, 15)
    
    # Créer l'embed
    embed = Embed(
        title=f"📊 STATISTIQUES DE {user.upper()}",
        color=rank_info['color'],
        timestamp=datetime.now()
    )
    
    # Section Niveau et Rang
    embed.add_field(
        name=f"{rank_info['emoji']} Niveau & Rang",
        value=f"**Niveau {player_data['level']}** - {rank_info['name']}\n"
              f"`{xp_progress}`\n"
              f"XP: {player_data['xp']}/{xp_for_next}",
        inline=False
    )
    
    # Section Performance
    embed.add_field(
        name="🎮 Performance",
        value=f"💎 **Points** : {player_data['points']}\n"
              f"🏆 **Classement** : {rank_display}\n"
              f"🎯 **Win Rate** : {win_rate}%",
        inline=True
    )
    
    # Section Parties
    embed.add_field(
        name="📈 Parties",
        value=f"🎲 **Jouées** : {player_data['parties_jouees']}\n"
              f"✅ **Gagnées** : {player_data['parties_gagnees']}\n"
              f"🔥 **Win Streak** : {player_data['win_streak']}",
        inline=True
    )
    
    # Section Records
    best_time_str = f"{player_data['best_time']:.2f}s" if player_data['best_time'] != float('inf') else "N/A"
    best_clicks_str = str(player_data['best_clicks']) if player_data['best_clicks'] != float('inf') else "N/A"
    
    embed.add_field(
        name="🏅 Records Personnels",
        value=f"⚡ **Meilleur temps** : {best_time_str}\n"
              f"🎯 **Moins de clics** : {best_clicks_str}\n"
              f"💎 **Meilleur score** : {player_data['best_score']}",
        inline=True
    )
    
    # Section Moyennes
    embed.add_field(
        name="📊 Moyennes",
        value=f"🖱️ **Clics** : {player_data['moyenne_clics']:.2f}\n"
              f"⏱️ **Temps** : {m_avg}m {s_avg}s\n"
              f"🗺️ **Articles visités** : {len(player_data.get('articles_visited', []))}",
        inline=True
    )
    
    # Section Temps total
    embed.add_field(
        name="⏳ Temps Total",
        value=f"**{h_total}h {m_total}m {s_total}s**",
        inline=True
    )
    
    # Section Achievements
    achievements_count = len(player_data.get('achievements', []))
    total_achievements = len(ACHIEVEMENTS)
    achievements_progress = get_progress_bar(achievements_count, total_achievements, 10)
    
    embed.add_field(
        name=f"🏆 Succès ({achievements_count}/{total_achievements})",
        value=f"`{achievements_progress}`",
        inline=False
    )
    
    embed.set_footer(
        text=f"Streak record: {player_data.get('best_win_streak', 0)} • En jeu depuis: {player_data.get('created_at', 'N/A')[:10]}"
    )
    
    await ctx.send(embed=embed)
    await ctx.message.delete()


@bot.command(name='achievements')
async def achievements(ctx, user: str = None):
    """Affiche les achievements d'un joueur"""
    
    if user is None:
        user = ctx.author.name
    
    player_data = PlayerData.load_player(user)
    
    if not player_data:
        await ctx.send(f"❌ Le joueur **{user}** n'existe pas !")
        await ctx.message.delete()
        return
    
    unlocked = player_data.get('achievements', [])
    rank_info = PlayerData.get_rank_info(player_data['level'])
    
    embed = Embed(
        title=f"🏆 SUCCÈS DE {user.upper()}",
        description=f"Débloquer des succès vous rapporte de l'XP bonus !",
        color=rank_info['color']
    )
    
    # Achievements débloqués
    unlocked_text = []
    for ach_id in unlocked:
        if ach_id in ACHIEVEMENTS:
            ach = ACHIEVEMENTS[ach_id]
            unlocked_text.append(f"{ach['name']}\n*{ach['description']}* (+{ach['xp']} XP)")
    
    if unlocked_text:
        embed.add_field(
            name=f"✅ Débloqués ({len(unlocked)}/{len(ACHIEVEMENTS)})",
            value="\n\n".join(unlocked_text) if unlocked_text else "Aucun",
            inline=False
        )
    
    # Achievements verrouillés
    locked_text = []
    for ach_id, ach in ACHIEVEMENTS.items():
        if ach_id not in unlocked:
            locked_text.append(f"🔒 {ach['name']}\n*{ach['description']}* (+{ach['xp']} XP)")
    
    if locked_text:
        embed.add_field(
            name=f"🔒 À débloquer ({len(locked_text)})",
            value="\n\n".join(locked_text[:5]),  # Limiter à 5 pour ne pas surcharger
            inline=False
        )
    
    progress = get_progress_bar(len(unlocked), len(ACHIEVEMENTS), 15)
    embed.add_field(
        name="📊 Progression",
        value=f"`{progress}`",
        inline=False
    )
    
    await ctx.send(embed=embed)
    await ctx.message.delete()


@bot.command(name='scoreboard')
async def scoreboard(ctx):
    """Affiche le classement des meilleurs joueurs"""
    
    players = PlayerData.get_all_players()
    
    if not players:
        await ctx.send("Aucun joueur enregistré !")
        await ctx.message.delete()
        return
    
    embed = Embed(
        title="🏆 CLASSEMENT GÉNÉRAL",
        description="Les meilleurs joueurs de Wikipédia Challenge",
        color=0xFFD700
    )
    
    for i, player in enumerate(players[:10], 1):
        rank_info = PlayerData.get_rank_info(player['level'])
        
        medal = ""
        if i == 1:
            medal = "🥇"
        elif i == 2:
            medal = "🥈"
        elif i == 3:
            medal = "🥉"
        else:
            medal = f"{i}."
        
        win_rate = 0
        if player['parties_jouees'] > 0:
            win_rate = round((player['parties_gagnees'] / player['parties_jouees']) * 100, 1)
        
        embed.add_field(
            name=f"{medal} {player['name']}",
            value=f"{rank_info['emoji']} Niv. {player['level']} • **{player['points']} pts**\n"
                  f"🎯 {win_rate}% WR • 🏆 {player['parties_gagnees']} victoires",
            inline=False
        )
    
    await ctx.send(embed=embed)
    await ctx.message.delete()


@bot.command(name='leaderboard')
async def leaderboard(ctx, category: str = "points"):
    """Affiche différents classements (points, niveau, winrate, etc.)"""
    
    players = PlayerData.get_all_players()
    
    if not players:
        await ctx.send("Aucun joueur enregistré !")
        await ctx.message.delete()
        return
    
    # Trier selon la catégorie
    if category.lower() in ["level", "niveau", "lvl"]:
        players.sort(key=lambda x: x['level'], reverse=True)
        title = "🎖️ CLASSEMENT PAR NIVEAU"
        emoji = "🆙"
    elif category.lower() in ["winrate", "wr", "victoires"]:
        for p in players:
            p['win_rate'] = (p['parties_gagnees'] / p['parties_jouees'] * 100) if p['parties_jouees'] > 0 else 0
        players.sort(key=lambda x: x['win_rate'], reverse=True)
        title = "📈 CLASSEMENT PAR WINRATE"
        emoji = "🎯"
    elif category.lower() in ["xp", "experience"]:
        players.sort(key=lambda x: x['xp'], reverse=True)
        title = "⭐ CLASSEMENT PAR XP"
        emoji = "✨"
    else:
        title = "💎 CLASSEMENT PAR POINTS"
        emoji = "💰"
    
    embed = Embed(
        title=title,
        color=0x6366F1
    )
    
    for i, player in enumerate(players[:10], 1):
        rank_info = PlayerData.get_rank_info(player['level'])
        
        if category.lower() in ["winrate", "wr", "victoires"]:
            value = f"{rank_info['emoji']} Niv. {player['level']} • **{player['win_rate']:.1f}% WR**\n"
        elif category.lower() in ["level", "niveau", "lvl"]:
            value = f"**Niveau {player['level']}** {rank_info['emoji']}\n{player['xp']} XP • {player['points']} points"
        elif category.lower() in ["xp", "experience"]:
            value = f"{rank_info['emoji']} **{player['xp']} XP**\nNiveau {player['level']} • {player['points']} points"
        else:
            value = f"{rank_info['emoji']} Niv. {player['level']} • **{player['points']} pts**"
        
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        
        embed.add_field(
            name=f"{medal} {player['name']}",
            value=value,
            inline=False
        )
    
    await ctx.send(embed=embed)
    await ctx.message.delete()


# ==================== COMMANDES - UTILITAIRES ====================


@bot.command(name='sommaire')
async def sommaire(ctx, *, args):
    """Envoie le sommaire d'un article en MP"""
    
    # Séparer les arguments
    parts = args.rsplit(maxsplit=1)
    
    # Vérifier si le dernier argument est un nombre
    if len(parts) == 2 and parts[1].isdigit():
        article = parts[0]
        nb_phrases = int(parts[1])
    else:
        article = args
        nb_phrases = 2
    
    try:
        channel = await ctx.author.create_dm()
        searching_msg = await channel.send("🔍 Recherche en cours...")
        
        results = wikipedia.search(article)
        
        if not results:
            await channel.send(f"❌ Aucun résultat pour **{article}**")
            await searching_msg.delete()
            await ctx.message.delete()
            return
        
        article_name = results[0]
        for result in results:
            if result.lower() == article.lower().replace('_', ' '):
                article_name = result
                break
        
        # Récupérer le sommaire
        try:
            summary = wikipedia.summary(article_name, nb_phrases)
        except DisambiguationError as e:
            article_name = e.options[0]
            summary = wikipedia.summary(article_name, nb_phrases)
        
        embed = Embed(
            title=f"📄 {article_name}",
            description=summary,
            color=0x3498db
        )
        embed.set_footer(text="Wikipédia Challenge")
        
        await channel.send(embed=embed)
        await searching_msg.delete()
        await ctx.message.delete()
        
    except PageError:
        await channel.send(f"❌ Article **{article}** introuvable")
        await searching_msg.delete()
    except Exception as e:
        await channel.send(f"❌ Erreur : {str(e)}")


@bot.command(name='guide')
async def guide(ctx):
    """Affiche le guide complet du bot"""
    
    embed = Embed(
        title="🌟 GUIDE WIKIPÉDIA CHALLENGE 🌟",
        description="Naviguez dans Wikipédia et progressez avec le système de niveaux !",
        color=0x6366F1
    )
    
    embed.set_thumbnail(
        url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/200px-Wikipedia-logo-v2.svg.png"
    )
    
    # Parties
    embed.add_field(
        name="🎮 JOUER",
        value="**%partie** - Créer une partie classée\n"
              "**%way** - Générer un parcours\n"
              "**%win <clics>** - Enregistrer votre victoire",
        inline=True
    )
    
    # Stats
    embed.add_field(
        name="📊 STATS",
        value="**%stats [joueur]** - Voir les statistiques\n"
              "**%achievements** - Vos succès\n"
              "**%scoreboard** - Top 10\n",
        inline=True
    )
    
    # Système de progression
    embed.add_field(
        name="⭐ SYSTÈME DE PROGRESSION",
        value="🥉 **Bronze** (Niv. 1-4)\n"
              "🥈 **Argent** (Niv. 5-9)\n"
              "🥇 **Or** (Niv. 10-14)\n"
              "💠 **Platine** (Niv. 15-17)\n"
              "💎 **Diamant** (Niv. 18-20)",
        inline=False
    )
    
    # Achievements
    embed.add_field(
        name="🏆 SUCCÈS À DÉBLOQUER",
        value="⚡ **Éclair** - Gagner en - 30s\n"
              "🎯 **Minimaliste** - Gagner en -3 clics\n"
              "🏃 **Marathon** - 10 parties d'affilée\n"
              "🗺️ **Explorateur** - 100 articles visités\n"
              "👑 **Perfectionniste** - 10 wins consécutives\n"
              "*Et bien d'autres...*",
        inline=False
    )
    
    # Utilitaires
    embed.add_field(
        name="🔧 UTILITAIRES",
        value="**%sommaire <article>** - Résumé en MP\n"
              "**%clear [n]** - Nettoyer le chat\n"
              "**%disconnect** - Éteindre le bot",
        inline=False
    )
    
    embed.set_footer(text="🎉 Gagnez de l'XP, montez de niveau et déverrouillez des succès ! 🎉")
    
    await ctx.send(embed=embed)
    await ctx.message.delete()


@bot.command(name='clear')
async def clear(ctx, nombre: int = 1):
    """Supprime des messages du salon"""
    try:
        deleted = await ctx.channel.purge(limit=nombre + 1)
        msg = await ctx.send(f"✅ {len(deleted) - 1} message(s) supprimé(s)")
        await asyncio.sleep(3)
        await msg.delete()
    except discord.Forbidden:
        await ctx.send("❌ Permissions insuffisantes !")
    except discord.HTTPException:
        await ctx.send("❌ Impossible de supprimer tous les messages")


        

@bot.command(name='status')
async def status(ctx):
    """Affiche le statut actuel de la partie"""
    
    embed = Embed(
        title="📊 STATUT DE LA PARTIE",
        color=0x6366F1
    )
    
    if game_session.enabled:
        embed.add_field(
            name="🟢 Statut",
            value="**Partie classée ACTIVE**",
            inline=False
        )
        
        if game_session.channel_id:
            channel = bot.get_channel(game_session.channel_id)
            if channel:
                embed.add_field(
                    name="🎤 Salon vocal",
                    value=f"**{channel.name}**",
                    inline=True
                )
        
        embed.add_field(
            name=f"👥 Joueurs ({len(game_session.members)})",
            value=format_player_list(game_session.members) if game_session.members else "Aucun",
            inline=True
        )
        
        if game_session.parcours:
            embed.add_field(
                name="🗺️ Parcours actif",
                value=f"De **{game_session.parcours[0].title}** à **{game_session.parcours[1].title}**",
                inline=False
            )
        
        if game_session.timer.start_time:
            elapsed = time.time() - game_session.timer.start_time
            embed.add_field(
                name="⏱️ Chrono",
                value=f"**{elapsed:.1f}s** en cours",
                inline=True
            )
    else:
        embed.add_field(
            name="🔴 Statut",
            value="**Aucune partie classée active**",
            inline=False
        )
    
    await ctx.send(embed=embed)
    await ctx.message.delete()



@bot.command(name='disconnect')
async def disconnect(ctx):
    """Déconnecte le bot"""
    await ctx.send("👋 **WikiBot** se déconnecte...")
    await ctx.message.delete()
    await bot.close()


# ==================== LANCEMENT ====================

if __name__ == "__main__":
    print("Démarrage de WikiBot...")
    bot.run(TOKEN)