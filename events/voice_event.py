#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Gestion des événements vocaux
"""


async def on_voice_state_update_handler(member, before, after, game_session, bot):
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