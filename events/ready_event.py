#! /usr/bin/python
# -*- coding: utf-8 -*-

"""
Événement de démarrage du bot
"""

import discord


async def on_ready_handler(bot):
    """Initialisation du bot"""
    print('━━━━━━━━━━━━━━━━━━━━━')
    print('WikiBot est en ligne !')
    print(f'User: {bot.user.name}')
    print(f'ID: {bot.user.id}')
    print('━━━━━━━━━━━━━━━━━━━━━')
