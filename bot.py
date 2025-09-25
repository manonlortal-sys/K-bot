import os
import discord
from discord.ext import commands
from discord import app_commands, Interaction, ui

# Variables d'environnement
TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))
CLIENT_ROLE_ID = int(os.getenv("CLIENT_ROLE_ID"))
PARTENAIRE_ROLE_ID = int(os.getenv("PARTENAIRE_ROLE_ID"))

intents = discord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

# ======================
# VUE DES BOUTONS
# ======================
class RoleButtons(ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @ui.button(label="CLIENT", style=discord.ButtonStyle.green, emoji="🎮")
    async def client_button(self, interaction: Interaction, button: ui.Button):
        if interaction.user != self.member:
            await interaction.response.send_message("Ce bouton n'est pas pour toi !", ephemeral=True)
            return
        role = interaction.guild.get_role(CLIENT_ROLE_ID)
        await self.member.add_roles(role)
        await interaction.response.send_message("Rôle CLIENT attribué !", ephemeral=True)
        # Désactive uniquement ce bouton
        button.disabled = True
        await interaction.message.edit(view=self)

    @ui.button(label="PARTENAIRE", style=discord.ButtonStyle.blurple, emoji="⭐")
    async def partenaire_button(self, interaction: Interaction, button: ui.Button):
        if interaction.user != self.member:
            await interaction.response.send_message("Ce bouton n'est pas pour toi !", ephemeral=True)
            return
        # Désactive uniquement ce bouton pour ce joueur
        button.disabled = True
        await interaction.message.edit(view=self)

        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        msg = f"{admin_role.mention}, {self.member.mention} a demandé le rôle PARTENAIRE. Merci de valider."
        validate_view = AdminValidation(self.member)
        await interaction.channel.send(msg, view=validate_view)
        await interaction.response.send_message("Votre demande PARTENAIRE a été envoyée aux admins.", ephemeral=True)

# ======================
# VALIDATION ADMIN
# ======================
class AdminValidation(ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @ui.button(label="Valider", style=discord.ButtonStyle.green)
    async def validate(self, interaction: Interaction, button: ui.Button):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role not in interaction.user.roles:
            await interaction.response.send_message("Seuls les admins peuvent valider.", ephemeral=True)
            return
        role = interaction.guild.get_role(PARTENAIRE_ROLE_ID)
        await self.member.add_roles(role)
        await interaction.response.send_message(f"Rôle PARTENAIRE attribué à {self.member.mention} !", ephemeral=True)
        # Supprime le message admin après validation
        await interaction.message.delete()

    @ui.button(label="Refuser", style=discord.ButtonStyle.red)
    async def refuse(self, interaction: Interaction, button: ui.Button):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role not in interaction.user.roles:
            await interaction.response.send_message("Seuls les admins peuvent refuser.", ephemeral=True)
            return
        await interaction.response.send_message(f"Demande PARTENAIRE de {self.member.mention} refusée.", ephemeral=True)
        # Supprime le message admin après refus
        await interaction.message.delete()

# ======================
# ACCUEIL DES MEMBRES
# ======================
@bot.event
async def on_member_join(member):
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    embed = discord.Embed(
        title="🎉 Bienvenue sur le serveur !",
        description=(
            f"Salut {member.mention} ! Clique sur le bouton correspondant au rôle que tu souhaites (tu peux en choisir plusieurs).\n\n"
            "⚠️ Si tu choisis le bouton 'Partenaire', un Admin vérifiera ta demande avant de valider.\n"
            "Une fois le rôle CLIENT attribué, tu auras accès au reste du discord !"
        ),
        color=discord.Color.orange()
    )
    embed.set_thumbnail(url="https://i.imgur.com/yourImage.png")  # remplace par ton image
    await channel.send(embed=embed, view=RoleButtons(member))

# ======================
# LANCEMENT DU BOT
# ======================
bot.run(TOKEN)
