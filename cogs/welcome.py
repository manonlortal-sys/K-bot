import os
import discord
from discord.ext import commands
from discord import Interaction, ui

# === Variables d'environnement ===
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID"))
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))
CLIENT_ROLE_ID = int(os.getenv("CLIENT_ROLE_ID"))
PARTENAIRE_ROLE_ID = int(os.getenv("PARTENAIRE_ROLE_ID"))


# ======================
# Vue des boutons (pour le membre)
# ======================
class RoleButtons(ui.View):
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member = member

    @ui.button(label="CLIENT", style=discord.ButtonStyle.green, emoji="💰")
    async def client_button(self, interaction: Interaction, button: ui.Button):
        if interaction.user != self.member:
            await interaction.response.send_message("Ce bouton n'est pas pour toi.", ephemeral=True)
            return

        role = interaction.guild.get_role(CLIENT_ROLE_ID)
        if role is None:
            await interaction.response.send_message(
                "Le rôle CLIENT est introuvable. Signale ceci à un administrateur.", ephemeral=True
            )
            return

        if role in self.member.roles:
            await interaction.response.send_message("Tu as déjà le rôle CLIENT.", ephemeral=True)
            button.disabled = True
            await interaction.message.edit(view=self)
            return

        try:
            await self.member.add_roles(role, reason="Auto-attribution via bouton CLIENT")
            await interaction.response.send_message("✅ Rôle **CLIENT** attribué !", ephemeral=True)
            button.disabled = True
            await interaction.message.edit(view=self)
        except discord.Forbidden:
            await interaction.response.send_message(
                "Je n'ai pas la permission d'attribuer ce rôle (vérifie l'ordre des rôles et la permission **Gérer les rôles**).",
                ephemeral=True,
            )

    @ui.button(label="PARTENAIRE", style=discord.ButtonStyle.blurple, emoji="⭐")
    async def partenaire_button(self, interaction: Interaction, button: ui.Button):
        if interaction.user != self.member:
            await interaction.response.send_message("Ce bouton n'est pas pour toi.", ephemeral=True)
            return

        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID)
        if admin_role is None:
            await interaction.response.send_message(
                "Le rôle administrateur à ping est introuvable. Signale ceci à un administrateur.", ephemeral=True
            )
            return

        button.disabled = True
        await interaction.message.edit(view=self)

        validate_view = AdminValidation(target_member=self.member)
        ping = f"{admin_role.mention}, {self.member.mention} a demandé le rôle **PARTENAIRE**. Merci de valider."
        admin_msg = await interaction.channel.send(ping, view=validate_view)
        validate_view.source_message_id = admin_msg.id

        await interaction.response.send_message(
            "📨 Ta demande **PARTENAIRE** a été transmise aux administrateurs.", ephemeral=True
        )


# ======================
# Vue de validation côté administrateurs
# ======================
class AdminValidation(ui.View):
    def __init__(self, target_member: discord.Member):
        super().__init__(timeout=None)
        self.target_member = target_member
        self.source_message_id: int | None = None

    def _is_admin(self, user: discord.Member) -> bool:
        admin_role = user.guild.get_role(ADMIN_ROLE_ID)
        return admin_role in getattr(user, "roles", [])

    async def _cleanup_admin_message(self, interaction: Interaction):
        try:
            if self.source_message_id:
                msg = await interaction.channel.fetch_message(self.source_message_id)
                await msg.delete()
        except Exception:
            pass

    @ui.button(label="Valider", style=discord.ButtonStyle.green, emoji="✅")
    async def validate(self, interaction: Interaction, button: ui.Button):
        if not self._is_admin(interaction.user):
            await interaction.response.send_message(
                "Seuls les administrateurs peuvent effectuer cette action.", ephemeral=True
            )
            return

        role = interaction.guild.get_role(PARTENAIRE_ROLE_ID)
        if role is None:
            await interaction.response.send_message("Le rôle PARTENAIRE est introuvable.", ephemeral=True)
            return

        try:
            await self.target_member.add_roles(role, reason=f"Validé par {interaction.user}")
            await interaction.response.send_message(
                f"Rôle **PARTENAIRE** attribué à {self.target_member.mention}.", ephemeral=True
            )
            await interaction.channel.send(
                f"{self.target_member.mention} ton rôle **PARTENAIRE** a été validé ✅", delete_after=10
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "Permission insuffisante pour attribuer le rôle (vérifie l'ordre des rôles).", ephemeral=True
            )

        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)
        await self._cleanup_admin_message(interaction)

    @ui.button(label="Refuser", style=discord.ButtonStyle.red, emoji="🛑")
    async def refuse(self, interaction: Interaction, button: ui.Button):
        if not self._is_admin(interaction.user):
            await interaction.response.send_message(
                "Seuls les administrateurs peuvent effectuer cette action.", ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Demande **PARTENAIRE** refusée pour {self.target_member.mention}.", ephemeral=True
        )
        await interaction.channel.send(
            f"{self.target_member.mention} ta demande **PARTENAIRE** a été refusée.", delete_after=10
        )

        for child in self.children:
            if isinstance(child, ui.Button):
                child.disabled = True
        await interaction.message.edit(view=self)
        await self._cleanup_admin_message(interaction)


# ======================
# Cog d’accueil
# ======================
class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        channel = self.bot.get_channel(WELCOME_CHANNEL_ID)
        if channel is None:
            return

        embed = discord.Embed(
            title="🎉 Bienvenue au K'rtel !",
            description=(
                f"👋 Salut {member.mention} !\n"
                "Choisis le rôle qui correspond à ton profil via les boutons ci-dessous. "
                "Tu peux sélectionner un ou les deux rôles selon tes besoins.\n\n"
                "⚠️ *Si tu demandes le rôle **Partenaire**, un administrateur examinera ta demande avant de la valider.*\n\n"
                "💰 **CLIENT** — Accès complet au serveur : discussions, échanges avec la communauté, commandes et infos utiles.\n"
                "⭐ **PARTENAIRE** — Tous les avantages de **Client** + accès au **canal partenaire** pour partager tes liens Discord "
                "et promouvoir tes activités (validation par un administrateur)."
            ),
            color=discord.Color.orange(),
        )

        embed.set_thumbnail(
            url="https://media.discordapp.net/attachments/1420787039346884778/1420788490035134484/Kbot_image_1-removebg-preview.png?ex=68d6abe4&is=68d55a64&hm=7448021bbf149ecf3e17145cb7ac3627b93560abe31248cb1e80f681ba94ab3b&=&format=webp&quality=lossless&width=233&height=459"
        )

        await channel.send(embed=embed, view=RoleButtons(member))


# ======================
# Setup du cog
# ======================
async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))

