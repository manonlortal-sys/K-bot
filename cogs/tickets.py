
import os
import datetime
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, TextStyle
from zoneinfo import ZoneInfo

# === IDs requis ===
HUB_CHANNEL_ID = 1420800148157759540            # salon où vit l'embed avec les 2 boutons
ARCHIVE_CHANNEL_ID = 1420800182513041498        # salon d'archives
TICKETS_CATEGORY_ID = 1420794008371990619       # catégorie où créer les tickets
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID")) # rôle admin (depuis l'env Render)

# === Custom IDs (vues persistantes) ===
CUSTOM_ID_OPEN_ACHAT = "ticket_open:achat"
CUSTOM_ID_OPEN_VENTE = "ticket_open:vente"
CUSTOM_ID_CLOSE = "ticket_close"

TZ_PARIS = ZoneInfo("Europe/Paris")


# ---------- helpers ----------
def _parse_kamas(text: str) -> int:
    # Garde uniquement les chiffres (supporte "12 500 000" -> 12500000)
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


# ========== Modal de fermeture ==========
class CloseTicketModal(ui.Modal, title="Fermeture du ticket"):
    def __init__(self, opener: discord.Member, is_achat: bool):
        super().__init__(timeout=180)
        self.opener = opener
        self.is_achat = is_achat

        # Champs à remplir par l'admin
        self.amount = ui.TextInput(
            label="Montant de la transaction (en kamas)",
            placeholder="Ex: 12 500 000",
            style=TextStyle.short,
            required=True,
            max_length=32,
        )
        self.rate = ui.TextInput(
            label="Taux de change (kamas/€)",
            placeholder="Ex: 5M/1€",
            style=TextStyle.short,
            required=True,
            max_length=32,
        )

        self.add_item(self.amount)
        self.add_item(self.rate)

    async def on_submit(self, interaction: Interaction):
        guild = interaction.guild
        if guild is None:
            return

        archive_ch = guild.get_channel(ARCHIVE_CHANNEL_ID)
        if archive_ch is None:
            await interaction.response.send_message(
                "Canal d’archives introuvable. Préviens un administrateur.", ephemeral=True
            )
            return

        admin = interaction.user
        # Heure en Europe/Paris
        now = datetime.datetime.now(TZ_PARIS).strftime("%d/%m/%Y %H:%M")
        kind = "achat" if self.is_achat else "vente"
        amount_int = _parse_kamas(self.amount.value)

        content = (
            f"**Transaction du {now} (heure de Paris)**\n"
            f"- Joueur : {self.opener.mention}\n"
            f"- Type : **{kind}**\n"
            f"- Montant : **{self.amount.value}** kamas\n"
            f"- Taux : **{self.rate.value}**\n"
            f"- Gérée par : {admin.mention}"
        )
        await archive_ch.send(content)

        # --- Mise à jour des stocks (cog Stocks) ---
        stocks_cog = interaction.client.get_cog("Stocks")
        if stocks_cog and amount_int > 0:
            try:
                await stocks_cog.apply_transaction(
                    guild=guild,
                    admin_member=admin if isinstance(admin, discord.Member) else guild.get_member(admin.id),
                    kind=kind,
                    amount=amount_int
                )
            except Exception:
                # On ne casse pas la fermeture de ticket si l'update stock échoue
                pass

        # Confirme puis supprime le ticket
        await interaction.response.send_message("Ticket archivé et fermé. Le salon va être supprimé.", ephemeral=True)
        try:
            await interaction.channel.delete(reason=f"Ticket {kind} fermé par {admin}")
        except discord.Forbidden:
            pass


# ========== View dans le ticket ==========
class TicketControls(ui.View):
    def __init__(self, opener: discord.Member, is_achat: bool):
        super().__init__(timeout=None)
        self.opener = opener
        self.is_achat = is_achat

    @ui.button(label="Fermeture ticket", style=discord.ButtonStyle.danger, custom_id=CUSTOM_ID_CLOSE, emoji="🔒")
    async def close_ticket(self, interaction: Interaction, button: ui.Button):
        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID) if interaction.guild else None
        if admin_role is None or admin_role not in getattr(interaction.user, "roles", []):
            await interaction.response.send_message("Seul un administrateur peut fermer ce ticket.", ephemeral=True)
            return

        await interaction.response.send_modal(CloseTicketModal(self.opener, self.is_achat))


# ========== View du hub ==========
class TicketHubView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="Achat de kamas", style=discord.ButtonStyle.green, emoji="💰", custom_id=CUSTOM_ID_OPEN_ACHAT)
    async def open_achat(self, interaction: Interaction, button: ui.Button):
        await self._open_ticket(interaction, is_achat=True)

    @ui.button(label="Vente de kamas", style=discord.ButtonStyle.blurple, emoji="⭐", custom_id=CUSTOM_ID_OPEN_VENTE)
    async def open_vente(self, interaction: Interaction, button: ui.Button):
        await self._open_ticket(interaction, is_achat=False)

    async def _open_ticket(self, interaction: Interaction, is_achat: bool):
        guild = interaction.guild
        user = interaction.user
        if guild is None or not isinstance(user, discord.Member):
            await interaction.response.send_message("Action impossible ici.", ephemeral=True)
            return

        category = guild.get_channel(TICKETS_CATEGORY_ID)
        if not isinstance(category, discord.CategoryChannel):
            await interaction.response.send_message("Catégorie de tickets introuvable.", ephemeral=True)
            return

        base = "ticket-achat" if is_achat else "ticket-vente"
        name = f"{base}-{user.name}".lower().replace(" ", "-")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
        }
        admin_role = guild.get_role(ADMIN_ROLE_ID)
        if admin_role is not None:
            overwrites[admin_role] = discord.PermissionOverwrite(
                view_channel=True, send_messages=True, manage_messages=True, attach_files=True, embed_links=True
            )

        channel = await guild.create_text_channel(name=name, category=category, overwrites=overwrites, reason="Ouverture ticket")
        ping = f"{user.mention} {admin_role.mention if admin_role else ''}".strip()
        title = "🎫 Ticket — Achat de kamas" if is_achat else "🎫 Ticket — Vente de kamas"
        desc = (
            "Merci d’avoir ouvert un ticket !\n\n"
            "👉 Indiquez précisément votre demande : **montant** que vous souhaitez "
            f"{'acheter' if is_achat else 'vendre'} (en kamas).\n\n"
            "⏳ Un administrateur va vous répondre. Merci de patienter.\n\n"
            "Quand l’échange est terminé, un **ADMIN** peut fermer le ticket avec le bouton ci-dessous."
        )
        embed = discord.Embed(title=title, description=desc, color=discord.Color.orange())
        await channel.send(content=ping, embed=embed, view=TicketControls(user, is_achat))

        await interaction.response.send_message(f"Ticket créé : {channel.mention}", ephemeral=True)


# ========== Cog ==========
class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Enregistre la vue persistante pour que les boutons du hub restent cliquables après redeploy
        self.bot.add_view(TicketHubView())

    # Slash command pour publier l'embed du hub
    @app_commands.command(name="publish_tickets", description="Publie le message avec les boutons de tickets")
    async def publish_tickets(self, interaction: Interaction):
        if not isinstance(interaction.user, discord.Member):
            return

        admin_role = interaction.guild.get_role(ADMIN_ROLE_ID) if interaction.guild else None
        if admin_role is None or admin_role not in getattr(interaction.user, "roles", []):
            await interaction.response.send_message("Seuls les administrateurs peuvent utiliser cette commande.", ephemeral=True)
            return

        hub = interaction.guild.get_channel(HUB_CHANNEL_ID)
        if hub is None:
            await interaction.response.send_message("Salon hub introuvable.", ephemeral=True)
            return

        embed = discord.Embed(
            title="🎟️ Support Kamas",
            description=(
                "Ouvrez un ticket en fonction de votre besoin :\n\n"
                "💰 **Achat de kamas**\n"
                "⭐ **Vente de kamas**\n\n"
                "Cliquez sur l’un des boutons ci-dessous."
            ),
            color=discord.Color.orange(),
        )
        await hub.send(embed=embed, view=TicketHubView())
        await interaction.response.send_message("✅ Message de tickets publié.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))

