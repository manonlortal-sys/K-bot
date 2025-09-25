# cogs/utils.py
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="envoyer", description="Fait envoyer un message par le bot dans un salon choisi.")
    @app_commands.describe(
        message="Le texte à envoyer",
        salon="Salon cible (par défaut : le salon où vous exécutez la commande)"
    )
    async def envoyer(self, interaction: discord.Interaction, message: str, salon: Optional[discord.TextChannel] = None):
        # Salon par défaut : celui où la commande est exécutée (si textuel)
        target = salon or interaction.channel

        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message(
                "Impossible d'envoyer ce message ici. Choisissez un salon textuel.",
                ephemeral=True
            )
            return

        try:
            sent = await target.send(message)
            await interaction.response.send_message(
                f"✅ Message envoyé dans {target.mention}.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Je n'ai pas la permission d'envoyer des messages dans ce salon.",
                ephemeral=True
            )
        except Exception:
            await interaction.response.send_message(
                "❌ Une erreur est survenue lors de l'envoi.",
                ephemeral=True
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
