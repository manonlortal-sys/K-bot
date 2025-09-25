import os
import sqlite3
import asyncio
from pathlib import Path
from typing import Optional, Tuple

import discord
from discord.ext import commands
from discord import app_commands
from zoneinfo import ZoneInfo
from datetime import datetime

# =========================
# Config & Constantes
# =========================
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))  # rôle admin (env Render)
GLOBAL_CHANNEL_ID = 1420819402198356082          # channel pour l'embed global
ADMINS_CHANNEL_ID = 1420820345891590316          # channel pour les embeds par admin

DB_PATH = Path("data/stocks.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

TZ_PARIS = ZoneInfo("Europe/Paris")


# =========================
# Helpers DB (synchro, wrap async)
# =========================
def _db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn

def _db_init():
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_global (
        guild_id INTEGER PRIMARY KEY,
        amount INTEGER NOT NULL DEFAULT 0,
        msg_channel_id INTEGER,
        msg_id INTEGER,
        updated_at TEXT
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_admin (
        guild_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        amount INTEGER NOT NULL DEFAULT 0,
        msg_channel_id INTEGER,
        msg_id INTEGER,
        updated_at TEXT,
        PRIMARY KEY (guild_id, admin_id)
    );
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_movements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        guild_id INTEGER NOT NULL,
        admin_id INTEGER,
        kind TEXT NOT NULL CHECK(kind IN ('achat','vente','manual')),
        amount INTEGER NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def _now_paris_str() -> str:
    return datetime.now(TZ_PARIS).strftime("%d/%m/%Y %H:%M")

def _select_global(guild_id: int) -> Tuple[int, Optional[int], Optional[int], Optional[str]]:
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("SELECT amount, msg_channel_id, msg_id, updated_at FROM stock_global WHERE guild_id=?;", (guild_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return int(row[0]), row[1], row[2], row[3]
    return 0, None, None, None

def _upsert_global(guild_id: int, amount: int, msg_channel_id: Optional[int], msg_id: Optional[int]) -> None:
    conn = _db_connect()
    cur = conn.cursor()
    now = _now_paris_str()
    cur.execute("""
        INSERT INTO stock_global(guild_id, amount, msg_channel_id, msg_id, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            amount=excluded.amount,
            msg_channel_id=COALESCE(excluded.msg_channel_id, stock_global.msg_channel_id),
            msg_id=COALESCE(excluded.msg_id, stock_global.msg_id),
            updated_at=excluded.updated_at;
    """, (guild_id, amount, msg_channel_id, msg_id, now))
    conn.commit()
    conn.close()

def _update_global_amount(guild_id: int, new_amount: int) -> None:
    conn = _db_connect()
    cur = conn.cursor()
    now = _now_paris_str()
    cur.execute("""
        INSERT INTO stock_global(guild_id, amount, updated_at)
        VALUES (?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            amount=excluded.amount,
            updated_at=excluded.updated_at;
    """, (guild_id, new_amount, now))
    conn.commit()
    conn.close()

def _insert_movement(guild_id: int, kind: str, amount: int, admin_id: Optional[int]) -> None:
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO stock_movements(guild_id, admin_id, kind, amount, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (guild_id, admin_id, kind, _abs(amount), datetime.now(TZ_PARIS).isoformat()))
    conn.commit()
    conn.close()

def _select_admin(guild_id: int, admin_id: int) -> Tuple[int, Optional[int], Optional[int], Optional[str]]:
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("""
        SELECT amount, msg_channel_id, msg_id, updated_at
        FROM stock_admin
        WHERE guild_id=? AND admin_id=?;
    """, (guild_id, admin_id))
    row = cur.fetchone()
    conn.close()
    if row:
        return int(row[0]), row[1], row[2], row[3]
    return 0, None, None, None

def _upsert_admin(guild_id: int, admin_id: int, amount: int, msg_channel_id: Optional[int], msg_id: Optional[int]) -> None:
    conn = _db_connect()
    cur = conn.cursor()
    now = _now_paris_str()
    cur.execute("""
        INSERT INTO stock_admin(guild_id, admin_id, amount, msg_channel_id, msg_id, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(guild_id, admin_id) DO UPDATE SET
            amount=excluded.amount,
            msg_channel_id=COALESCE(excluded.msg_channel_id, stock_admin.msg_channel_id),
            msg_id=COALESCE(excluded.msg_id, stock_admin.msg_id),
            updated_at=excluded.updated_at;
    """, (guild_id, admin_id, amount, msg_channel_id, msg_id, now))
    conn.commit()
    conn.close()

def _update_admin_amount(guild_id: int, admin_id: int, new_amount: int) -> None:
    conn = _db_connect()
    cur = conn.cursor()
    now = _now_paris_str()
    cur.execute("""
        INSERT INTO stock_admin(guild_id, admin_id, amount, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id, admin_id) DO UPDATE SET
            amount=excluded.amount,
            updated_at=excluded.updated_at;
    """, (guild_id, admin_id, new_amount, now))
    conn.commit()
    conn.close()

def _abs(x: int) -> int:
    return x if x >= 0 else -x


# =========================
# Embeds builders
# =========================
def _embed_global(amount: int, updated_at: Optional[str]) -> discord.Embed:
    title = "💰✨ 𝗦𝗧𝗢𝗖𝗞𝗦 𝗞𝗔𝗠𝗔𝗦 ✨💰"
    desc = (
        f"📊 **Stock disponible :** {amount:,} kamas\n"
        f"🕒 **Dernière mise à jour :** {updated_at or _now_paris_str()} (heure de Paris)"
    )
    color = discord.Color.green() if amount > 0 else discord.Color.red()
    e = discord.Embed(title=title, description=desc, color=color)
    return e

def _embed_admin(member: discord.Member, amount: int, updated_at: Optional[str]) -> discord.Embed:
    title = f"👤 𝗦𝗧𝗢𝗖𝗞 — {member.display_name}"
    desc = (
        f"📦 **Stock (transactions gérées par {member.mention}) :** {amount:,} kamas\n"
        f"🕒 **Dernière mise à jour :** {updated_at or _now_paris_str()} (heure de Paris)"
    )
    e = discord.Embed(title=title, description=desc, color=discord.Color.blue())
    e.set_thumbnail(url=member.display_avatar.url if member.display_avatar else discord.Embed.Empty)
    return e


# =========================
# Cog Stocks
# =========================
class Stocks(commands.Cog):
    """Gestion des stocks (global + par admin) avec embeds fixes et SQLite."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Init DB au chargement du cog
        await self.bot.loop.run_in_executor(None, _db_init)

    # -------------------------
    # Méthode publique pour tickets
    # -------------------------
    async def apply_transaction(self, guild: discord.Guild, admin_member: discord.Member, kind: str, amount: int):
        """
        À appeler depuis le cog tickets à la fermeture:
          - kind: 'achat' (stock +) ou 'vente' (stock -)
          - amount: montant en kamas (positif)
        Met à jour: stock global + stock de l'admin + édite les embeds si disponibles.
        """
        if kind not in ("achat", "vente"):
            return

        sign = 1 if kind == "achat" else -1
        delta = sign * amount
        guild_id = guild.id
        admin_id = admin_member.id

        # --- GLOBAL ---
        current_global, g_ch_id, g_msg_id, _g_upd = await self.bot.loop.run_in_executor(None, _select_global, guild_id)
        new_global = current_global + delta
        await self.bot.loop.run_in_executor(None, _update_global_amount, guild_id, new_global)
        await self.bot.loop.run_in_executor(None, _insert_movement, guild_id, kind, amount, admin_id)

        # Edit embed global si message connu
        if g_ch_id and g_msg_id:
            ch = guild.get_channel(g_ch_id)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(g_msg_id)
                    e = _embed_global(new_global, _now_paris_str())
                    await msg.edit(embed=e)
                except discord.NotFound:
                    pass

        # --- ADMIN ---
        curr_admin, a_ch_id, a_msg_id, _a_upd = await self.bot.loop.run_in_executor(None, _select_admin, guild_id, admin_id)
        new_admin = curr_admin + delta
        await self.bot.loop.run_in_executor(None, _update_admin_amount, guild_id, admin_id, new_admin)

        # Edit embed admin si message connu
        if a_ch_id and a_msg_id:
            ch2 = guild.get_channel(a_ch_id)
            if isinstance(ch2, (discord.TextChannel, discord.Thread)):
                try:
                    msg2 = await ch2.fetch_message(a_msg_id)
                    e2 = _embed_admin(admin_member, new_admin, _now_paris_str())
                    await msg2.edit(embed=e2)
                except discord.NotFound:
                    pass

    # -------------------------
    # Guards
    # -------------------------
    def _is_admin_member(self, member: discord.Member) -> bool:
        role = member.guild.get_role(ADMIN_ROLE_ID) if member and member.guild else None
        return role in getattr(member, "roles", [])

    # -------------------------
    # Slash: publication des messages fixes
    # -------------------------
    @app_commands.command(name="stock_publish_global", description="Créer le message fixe du stock global (embed) dans le channel configuré.")
    async def stock_publish_global(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

        channel = guild.get_channel(GLOBAL_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Channel global introuvable.", ephemeral=True)
            return

        # Upsert ligne globale si besoin
        amount, _, _, updated_at = await self.bot.loop.run_in_executor(None, _select_global, guild.id)
        embed = _embed_global(amount, updated_at)

        msg = await channel.send(embed=embed)
        await self.bot.loop.run_in_executor(None, _upsert_global, guild.id, amount, channel.id, msg.id)

        await interaction.response.send_message("✅ Message de stock global publié.", ephemeral=True)

    @app_commands.command(name="stock_publish_admin", description="Créer le message fixe du stock d'un admin (embed) dans le channel des admins.")
    @app_commands.describe(admin="Sélectionnez l'administrateur")
    async def stock_publish_admin(self, interaction: discord.Interaction, admin: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

        # Vérifie que la cible a bien le rôle admin
        if not self._is_admin_member(admin):
            await interaction.response.send_message("Le membre sélectionné n'a pas le rôle ADMIN.", ephemeral=True)
            return

        channel = guild.get_channel(ADMINS_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message("Channel des stocks admins introuvable.", ephemeral=True)
            return

        amount, _, _, updated_at = await self.bot.loop.run_in_executor(None, _select_admin, guild.id, admin.id)
        embed = _embed_admin(admin, amount, updated_at)

        msg = await channel.send(embed=embed)
        await self.bot.loop.run_in_executor(None, _upsert_admin, guild.id, admin.id, amount, channel.id, msg.id)

        await interaction.response.send_message(f"✅ Message de stock créé pour {admin.mention}.", ephemeral=True)

    # -------------------------
    # Slash: ajustements manuels GLOBAL
    # -------------------------
    @app_commands.command(name="stock_set", description="Fixer le stock global à un montant exact.")
    @app_commands.describe(montant="Montant en kamas (entier, ex: 12500000)")
    async def stock_set(self, interaction: discord.Interaction, montant: app_commands.Range[int, 0]):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

        await self.bot.loop.run_in_executor(None, _update_global_amount, guild.id, int(montant))
        await self.bot.loop.run_in_executor(None, _insert_movement, guild.id, "manual", int(montant), interaction.user.id)

        # Edit embed si connu
        amount, g_ch, g_msg, upd = await self.bot.loop.run_in_executor(None, _select_global, guild.id)
        if g_ch and g_msg:
            ch = guild.get_channel(g_ch)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(g_msg)
                    await msg.edit(embed=_embed_global(amount, upd))
                except discord.NotFound:
                    pass

        await interaction.response.send_message(f"✅ Stock global fixé à {amount:,} kamas.", ephemeral=True)

    @app_commands.command(name="stock_add", description="Augmenter le stock global.")
    @app_commands.describe(montant="Montant en kamas à ajouter")
    async def stock_add(self, interaction: discord.Interaction, montant: app_commands.Range[int, 1]):
        await self._adjust_global(interaction, int(montant))

    @app_commands.command(name="stock_remove", description="Diminuer le stock global.")
    @app_commands.describe(montant="Montant en kamas à retirer")
    async def stock_remove(self, interaction: discord.Interaction, montant: app_commands.Range[int, 1]):
        await self._adjust_global(interaction, -int(montant))

    async def _adjust_global(self, interaction: discord.Interaction, delta: int):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return
        guild = interaction.guild
        if guild is None:
            return

        current, _, _, _ = await self.bot.loop.run_in_executor(None, _select_global, guild.id)
        new_amount = current + delta
        if new_amount < 0:
            new_amount = 0
        await self.bot.loop.run_in_executor(None, _update_global_amount, guild.id, new_amount)
        await self.bot.loop.run_in_executor(None, _insert_movement, guild.id, "manual", _abs(delta), interaction.user.id)

        amount, g_ch, g_msg, upd = await self.bot.loop.run_in_executor(None, _select_global, guild.id)
        if g_ch and g_msg:
            ch = guild.get_channel(g_ch)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(g_msg)
                    await msg.edit(embed=_embed_global(amount, upd))
                except discord.NotFound:
                    pass

        sign = "+" if delta >= 0 else "-"
        await interaction.response.send_message(f"✅ Stock global ajusté ({sign}{_abs(delta):,}). Nouveau stock : {amount:,} kamas.", ephemeral=True)

    # -------------------------
    # Slash: ajustements manuels par ADMIN
    # -------------------------
    @app_commands.command(name="stock_set_admin", description="Fixer le stock d'un admin à un montant exact.")
    @app_commands.describe(admin="Administrateur cible", montant="Montant en kamas")
    async def stock_set_admin(self, interaction: discord.Interaction, admin: discord.Member, montant: app_commands.Range[int, 0]):
        await self._set_admin_amount(interaction, admin, int(montant))

    @app_commands.command(name="stock_add_admin", description="Augmenter le stock d'un admin.")
    @app_commands.describe(admin="Administrateur cible", montant="Montant en kamas à ajouter")
    async def stock_add_admin(self, interaction: discord.Interaction, admin: discord.Member, montant: app_commands.Range[int, 1]):
        await self._adjust_admin(interaction, admin, int(montant))

    @app_commands.command(name="stock_remove_admin", description="Diminuer le stock d'un admin.")
    @app_commands.describe(admin="Administrateur cible", montant="Montant en kamas à retirer")
    async def stock_remove_admin(self, interaction: discord.Interaction, admin: discord.Member, montant: app_commands.Range[int, 1]):
        await self._adjust_admin(interaction, admin, -int(montant))

    async def _set_admin_amount(self, interaction: discord.Interaction, admin: discord.Member, new_amount: int):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return
        if not self._is_admin_member(admin):
            await interaction.response.send_message("Le membre sélectionné n'a pas le rôle ADMIN.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

        await self.bot.loop.run_in_executor(None, _update_admin_amount, guild.id, admin.id, new_amount)
        await self.bot.loop.run_in_executor(None, _insert_movement, guild.id, "manual", new_amount, admin.id)

        amount, ch_id, msg_id, upd = await self.bot.loop.run_in_executor(None, _select_admin, guild.id, admin.id)
        if ch_id and msg_id:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(msg_id)
                    await msg.edit(embed=_embed_admin(admin, amount, upd))
                except discord.NotFound:
                    pass

        await interaction.response.send_message(f"✅ Stock de {admin.mention} fixé à {new_amount:,} kamas.", ephemeral=True)

    async def _adjust_admin(self, interaction: discord.Interaction, admin: discord.Member, delta: int):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return
        if not self._is_admin_member(admin):
            await interaction.response.send_message("Le membre sélectionné n'a pas le rôle ADMIN.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

        current, _, _, _ = await self.bot.loop.run_in_executor(None, _select_admin, guild.id, admin.id)
        new_amount = current + delta
        if new_amount < 0:
            new_amount = 0
        await self.bot.loop.run_in_executor(None, _update_admin_amount, guild.id, admin.id, new_amount)
        await self.bot.loop.run_in_executor(None, _insert_movement, guild.id, "manual", _abs(delta), admin.id)

        amount, ch_id, msg_id, upd = await self.bot.loop.run_in_executor(None, _select_admin, guild.id, admin.id)
        if ch_id and msg_id:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(msg_id)
                    await msg.edit(embed=_embed_admin(admin, amount, upd))
                except discord.NotFound:
                    pass

        sign = "+" if delta >= 0 else "-"
        await interaction.response.send_message(
            f"✅ Stock de {admin.mention} ajusté ({sign}{_abs(delta):,}). Nouveau stock : {amount:,} kamas.",
            ephemeral=True
        )


# =========================
# Setup
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))

Intégration (quand tu voudras l’ajouter dans tickets.py)

Dans ton handler de fermeture (après avoir déterminé kind = "achat"/"vente" et amount), tu pourras appeler :

stocks_cog = interaction.client.get_cog("Stocks")
if stocks_cog:
    await stocks_cog.apply_transaction(interaction.guild, interaction.user, kind, amount)
