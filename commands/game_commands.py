import discord
import asyncio
from discord import app_commands
from discord.ext import commands


def setup_game_commands(bot, game_session, player_service, game_service, 
                       wikipedia_service, embed_creator, formatters, validators):
    """Configure les commandes de jeu en slash commands"""
    
    @bot.tree.command(name='partie', description='Démarre une partie classée')
    async def partie(interaction: discord.Interaction):
        """Démarre une partie classée"""
        
        if not validators.is_in_voice_channel(interaction.user):
            embed = embed_creator.create_error_embed(
                "Vous devez être connecté à un salon vocal !"
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        try:
            channel = interaction.user.voice.channel
            human_members = validators.get_human_members(channel)
            
            if not human_members:
                embed = embed_creator.create_error_embed(
                    "Aucun joueur humain détecté dans le salon vocal."
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Si une partie est déjà active dans ce salon
            if game_session.enabled and game_session.channel_id == channel.id:
                embed = embed_creator.create_warning_embed(
                    "Partie déjà active",
                    f"Une partie classée est déjà en cours dans **{channel.name}**"
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            # Confirmation pour partie solo
            if len(human_members) < 2:
                embed = embed_creator.create_warning_embed(
                    "Partie solo",
                    f"Vous êtes seul dans **{channel.name}**.\nVoulez-vous continuer ?"
                )
                
                # Créer une vue avec des boutons
                class ConfirmView(discord.ui.View):
                    def __init__(self):
                        super().__init__(timeout=30.0)
                        self.value = None
                    
                    @discord.ui.button(label='Confirmer', style=discord.ButtonStyle.success, emoji='✅')
                    async def confirm(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        self.value = True
                        self.stop()
                        await button_interaction.response.defer()
                    
                    @discord.ui.button(label='Annuler', style=discord.ButtonStyle.danger, emoji='❌')
                    async def cancel(self, button_interaction: discord.Interaction, button: discord.ui.Button):
                        self.value = False
                        self.stop()
                        await button_interaction.response.defer()
                
                view = ConfirmView()
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                await view.wait()
                
                if not view.value:
                    embed = embed_creator.create_error_embed("🚫 Annulé")
                    await interaction.edit_original_response(embed=embed, view=None)
                    return
            else:
                await interaction.response.defer()
            
            # Initialiser la session
            from datetime import datetime
            game_session.members = [m.name for m in human_members]
            game_session.enabled = True
            game_session.channel_id = channel.id
            game_session.start_time = datetime.now()
            
            new_players = []
            
            for member_name in game_session.members:
                player_data = player_service.get_player(member_name)
                if not player_data:
                    player_service.create_player(member_name)
                    new_players.append(member_name)
            
            # Créer l'embed de partie
            embed = embed_creator.create_game_created_embed(
                channel.name, 
                game_session.members, 
                new_players, 
                interaction.user,
                formatters
            )
            
            if len(human_members) < 2:
                await interaction.edit_original_response(embed=embed, view=None)
            else:
                await interaction.followup.send(embed=embed)
            
        except Exception as e:
            embed = embed_creator.create_error_embed(f"```{str(e)}```")
            if interaction.response.is_done():
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @bot.tree.command(name='way', description='Génère un parcours Wikipédia aléatoire')
    async def way(interaction: discord.Interaction):
        """Génère un parcours Wikipédia aléatoire"""
        
        if not game_session.enabled:
            await interaction.response.send_message(
                "⚠️ **Partie non classée**\n"
                "🔄 Génération du parcours..."
            )
        else:
            await interaction.response.send_message("🔄 Génération du parcours...")
        
        result = wikipedia_service.generate_path(max_attempts=10)
        
        if result is None:
            await interaction.edit_original_response(
                content="🔴 Impossible de générer un parcours après 10 tentatives."
            )
            return
        
        page1, page_target, attempt = result
        game_session.parcours = [page1, page_target]
        
        # Créer l'embed du parcours
        embed = embed_creator.create_path_embed(
            page1, 
            page_target, 
            game_session.enabled, 
            attempt
        )
        
        msg = await interaction.edit_original_response(content=None, embed=embed)
        
        await msg.add_reaction("🔄")
        await msg.add_reaction("✅")
    
    @bot.tree.command(name='win', description='Enregistre votre victoire')
    @app_commands.describe(clicks='Nombre de clics effectués')
    async def win(interaction: discord.Interaction, clicks: int):
        """Enregistre la victoire avec calcul de points et XP"""
        
        if not game_session.enabled:
            await interaction.response.send_message(
                "⚠️ Partie non classée - score non enregistrable !",
                ephemeral=True
            )
            return
        
        if interaction.user != game_session.winner:
            await interaction.response.send_message(
                f"❌ {interaction.user.mention} n'est pas le gagnant !",
                ephemeral=True
            )
            return
        
        if clicks <= 0:
            await interaction.response.send_message(
                "❌ Le nombre de clics doit être un nombre positif !",
                ephemeral=True
            )
            return
        
        try:
            await interaction.response.defer()
            
            winner_name = game_session.winner.name
            temps = float(game_session.timer.duration)
            
            # Enregistrer la victoire
            articles = (game_session.parcours[0].title, game_session.parcours[1].title)
            result = game_service.register_win(
                winner_name, 
                temps, 
                clicks, 
                articles, 
                game_session.members
            )
            
            result['temps'] = temps
            result['clicks'] = clicks
            
            # Obtenir les infos de rang
            rank_info = player_service.get_rank_info(result['player_data']['level'])
            
            # Créer l'embed de victoire
            embed = embed_creator.create_victory_embed(
                game_session.winner,
                result,
                rank_info,
                formatters
            )
            
            await interaction.followup.send(embed=embed)
            
            game_session.reset_round()
            
        except Exception as e:
            await interaction.followup.send(f"🔴 Erreur : {str(e)}", ephemeral=True)
    
    return partie, way, win