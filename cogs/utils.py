# cogs/utils.py
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

def _parse_hex_color(value: Optional[str]) -> Optional[discord.Color]:
    if not value:
        return None
    v = value.strip().lstrip("#")
    try:
        return discord.Color(int(v, 16))
    except ValueError:
        return None

class Utils(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # /envoyer — message texte simple
    @app_commands.command(name="envoyer", description="Fait envoyer un message texte par le bot dans un salon choisi.")
    @app_commands.describe(
        message="Le texte à envoyer",
        salon="Salon cible (par défaut : le salon où la commande est exécutée)"
    )
    async def envoyer(self, interaction: discord.Interaction, message: str, salon: Optional[discord.TextChannel] = None):
        target = salon or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("Choisissez un salon textuel.", ephemeral=True)
            return
        try:
            await target.send(message)
            await interaction.response.send_message(f"✅ Message envoyé dans {target.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permissions insuffisantes dans ce salon.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Erreur lors de l’envoi.", ephemeral=True)

    # /envoyer_embed — embed personnalisable
    @app_commands.command(name="envoyer_embed", description="Envoie un embed personnalisé via le bot.")
    @app_commands.describe(
        titre="Titre de l'embed",
        description="Description (texte principal) de l'embed",
        couleur_hex="Couleur hexadécimale (ex: #ff9900) — optionnel",
        salon="Salon cible (par défaut : le salon où la commande est exécutée)",
        image_url="URL d'image (optionnel)",
        thumbnail_url="URL de vignette (optionnel)",
        footer="Texte de pied de page (optionnel)"
    )
    async def envoyer_embed(
        self,
        interaction: discord.Interaction,
        titre: str,
        description: str,
        couleur_hex: Optional[str] = None,
        salon: Optional[discord.TextChannel] = None,
        image_url: Optional[str] = None,
        thumbnail_url: Optional[str] = None,
        footer: Optional[str] = None,
    ):
        target = salon or interaction.channel
        if not isinstance(target, discord.TextChannel):
            await interaction.response.send_message("Choisissez un salon textuel.", ephemeral=True)
            return

        color = _parse_hex_color(couleur_hex) or discord.Color.blurple()
        embed = discord.Embed(title=titre, description=description, color=color)

        if image_url:
            embed.set_image(url=image_url)
        if thumbnail_url:
            embed.set_thumbnail(url=thumbnail_url)
        if footer:
            embed.set_footer(text=footer)

        try:
            await target.send(embed=embed)
            await interaction.response.send_message(f"✅ Embed envoyé dans {target.mention}.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permissions insuffisantes dans ce salon.", ephemeral=True)
        except Exception:
            await interaction.response.send_message("❌ Erreur lors de l’envoi de l’embed.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Utils(bot))
