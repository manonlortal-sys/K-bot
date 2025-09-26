# cogs/stocks.py
import os
import sqlite3
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
# Helpers DB
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

def _upsert_global_meta(guild_id: int, amount: int, msg_channel_id: Optional[int], msg_id: Optional[int]) -> None:
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
    """, (guild_id, admin_id, kind, abs(amount), datetime.now(TZ_PARIS).isoformat()))
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

def _sum_admins(guild_id: int) -> int:
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(amount),0) FROM stock_admin WHERE guild_id=?;", (guild_id,))
    (total,) = cur.fetchone()
    conn.close()
    return int(total or 0)


# =========================
# Embeds
# =========================
def _embed_global(amount: int, updated_at: Optional[str]) -> discord.Embed:
    title = "💰✨ 𝗦𝗧𝗢𝗖𝗞𝗦 𝗞𝗔𝗠𝗔𝗦 ✨💰"
    desc = (
        f"📊 **Stock disponible :** {amount:,} kamas\n"
        f"🕒 **Dernière mise à jour :** {updated_at or _now_paris_str()} (heure de Paris)"
    )
    color = discord.Color.green() if amount > 0 else discord.Color.red()
    return discord.Embed(title=title, description=desc, color=color)

def _embed_admin(member: discord.Member, amount: int, updated_at: Optional[str]) -> discord.Embed:
    title = f"👤 𝗦𝗧𝗢𝗖𝗞 — {member.display_name}"
    desc = (
        f"📦 **Stock (transactions gérées par {member.mention}) :** {amount:,} kamas\n"
        f"🕒 **Dernière mise à jour :** {updated_at or _now_paris_str()} (heure de Paris)"
    )
    e = discord.Embed(title=title, description=desc, color=discord.Color.blue())
    try:
        e.set_thumbnail(url=member.display_avatar.url)
    except Exception:
        pass
    return e


# =========================
# Cog Stocks
# =========================
class Stocks(commands.Cog):
    """Stock global = somme des stocks des admins. Embeds fixes, SQLite."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        await self.bot.loop.run_in_executor(None, _db_init)

    # ----- helper central : recompute global & refresh embed -----
    async def _recompute_and_refresh_global(self, guild: discord.Guild):
        total = await self.bot.loop.run_in_executor(None, _sum_admins, guild.id)
        await self.bot.loop.run_in_executor(None, _update_global_amount, guild.id, total)

        amount, ch_id, msg_id, upd = await self.bot.loop.run_in_executor(None, _select_global, guild.id)
        if ch_id and msg_id:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(msg_id)
                    await msg.edit(embed=_embed_global(amount, upd))
                except discord.NotFound:
                    pass

    # ----- appelée depuis le cog tickets -----
    async def apply_transaction(self, guild: discord.Guild, admin_member: discord.Member, kind: str, amount: int):
        """
        kind: 'achat' (+=) ou 'vente' (-=), amount > 0
        Met à jour le stock de l'admin, enregistre mouvement, puis recalcule le global.
        """
        if kind not in ("achat", "vente") or amount <= 0:
            return

        guild_id = guild.id
        admin_id = admin_member.id

        # admin courant
        curr_admin, _, _, _ = await self.bot.loop.run_in_executor(None, _select_admin, guild_id, admin_id)
        delta = amount if kind == "achat" else -amount
        new_admin = max(0, curr_admin + delta)
        await self.bot.loop.run_in_executor(None, _update_admin_amount, guild_id, admin_id, new_admin)
        await self.bot.loop.run_in_executor(None, _insert_movement, guild_id, kind, amount, admin_id)

        # refresh embed admin si connu
        a_amount, a_ch_id, a_msg_id, a_upd = await self.bot.loop.run_in_executor(None, _select_admin, guild_id, admin_id)
        if a_ch_id and a_msg_id:
            ch2 = guild.get_channel(a_ch_id)
            if isinstance(ch2, (discord.TextChannel, discord.Thread)):
                try:
                    msg2 = await ch2.fetch_message(a_msg_id)
                    await msg2.edit(embed=_embed_admin(admin_member, a_amount, a_upd))
                except discord.NotFound:
                    pass

        # recalcule le global
        await self._recompute_and_refresh_global(guild)

    # -------------------------
    # Guards
    # -------------------------
    def _is_admin_member(self, member: discord.Member) -> bool:
        role = member.guild.get_role(ADMIN_ROLE_ID) if member and member.guild else None
        return role in getattr(member, "roles", [])

    # -------------------------
    # Publication des messages fixes
    # -------------------------
    @app_commands.command(name="stock_publish_global", description="Créer/relier le message fixe du stock global.")
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

        total = await self.bot.loop.run_in_executor(None, _sum_admins, guild.id)
        embed = _embed_global(total, _now_paris_str())
        msg = await channel.send(embed=embed)
        await self.bot.loop.run_in_executor(None, _upsert_global_meta, guild.id, total, channel.id, msg.id)

        await interaction.response.send_message("✅ Message de stock global publié et lié.", ephemeral=True)

    @app_commands.command(name="stock_publish_admin", description="Créer/relier le message fixe du stock d'un admin.")
    @app_commands.describe(admin="Administrateur cible")
    async def stock_publish_admin(self, interaction: discord.Interaction, admin: discord.Member):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

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
    # Ajustements MANUELS côté ADMIN (impactent le global)
    # -------------------------
    @app_commands.command(name="stock_set_admin", description="Fixer le stock d'un admin (impacte le global).")
    @app_commands.describe(admin="Administrateur cible", montant="Montant en kamas")
    async def stock_set_admin(self, interaction: discord.Interaction, admin: discord.Member, montant: app_commands.Range[int, 0]):
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
        await self.bot.loop.run_in_executor(None, _update_admin_amount, guild.id, admin.id, int(montant))
        await self.bot.loop.run_in_executor(None, _insert_movement, guild.id, "manual", abs(int(montant) - current), admin.id)

        # refresh embed admin
        amount, ch_id, msg_id, upd = await self.bot.loop.run_in_executor(None, _select_admin, guild.id, admin.id)
        if ch_id and msg_id:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(msg_id)
                    await msg.edit(embed=_embed_admin(admin, amount, upd))
                except discord.NotFound:
                    pass

        # recalcule le global
        await self._recompute_and_refresh_global(guild)
        await interaction.response.send_message(f"✅ Stock de {admin.mention} fixé à {amount:,} kamas (global mis à jour).", ephemeral=True)

    @app_commands.command(name="stock_add_admin", description="Augmenter le stock d'un admin (impacte le global).")
    @app_commands.describe(admin="Administrateur cible", montant="Montant en kamas à ajouter")
    async def stock_add_admin(self, interaction: discord.Interaction, admin: discord.Member, montant: app_commands.Range[int, 1]):
        await self._adjust_admin(interaction, admin, int(montant))

    @app_commands.command(name="stock_remove_admin", description="Diminuer le stock d'un admin (impacte le global).")
    @app_commands.describe(admin="Administrateur cible", montant="Montant en kamas à retirer")
    async def stock_remove_admin(self, interaction: discord.Interaction, admin: discord.Member, montant: app_commands.Range[int, 1]):
        await self._adjust_admin(interaction, admin, -int(montant))

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
        new_amount = max(0, current + delta)
        await self.bot.loop.run_in_executor(None, _update_admin_amount, guild.id, admin.id, new_amount)
        await self.bot.loop.run_in_executor(None, _insert_movement, guild.id, "manual", abs(delta), admin.id)

        # refresh embed admin
        amount, ch_id, msg_id, upd = await self.bot.loop.run_in_executor(None, _select_admin, guild.id, admin.id)
        if ch_id and msg_id:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, (discord.TextChannel, discord.Thread)):
                try:
                    msg = await ch.fetch_message(msg_id)
                    await msg.edit(embed=_embed_admin(admin, amount, upd))
                except discord.NotFound:
                    pass

        # recalcule le global
        await self._recompute_and_refresh_global(guild)
        sign = "+" if delta >= 0 else "-"
        await interaction.response.send_message(
            f"✅ Stock de {admin.mention} ajusté ({sign}{abs(delta):,}). Nouveau : {amount:,} kamas (global mis à jour).",
            ephemeral=True
        )

    # -------------------------
    # Refresh manuel complet
    # -------------------------
    @app_commands.command(name="stock_refresh", description="Recalcule le stock global à partir des admins et réédite l'embed global.")
    async def stock_refresh(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not self._is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return
        if interaction.guild is None:
            return
        await self._recompute_and_refresh_global(interaction.guild)
        await interaction.response.send_message("🔄 Stock global recalculé et rafraîchi.", ephemeral=True)

    # -------------------------
    # Désactivation des commandes globales directes
    # -------------------------
    @app_commands.command(name="stock_set", description="(Désactivé) Le stock global est la somme des stocks admins.")
    async def stock_set(self, interaction: discord.Interaction, montant: int):
        await interaction.response.send_message("❌ Le stock global est calculé automatiquement (somme des stocks admins). Utilisez les commandes *_admin.", ephemeral=True)

    @app_commands.command(name="stock_add", description="(Désactivé) Le stock global est la somme des stocks admins.")
    async def stock_add(self, interaction: discord.Interaction, montant: int):
        await interaction.response.send_message("❌ Le stock global est calculé automatiquement (somme des stocks admins). Utilisez les commandes *_admin.", ephemeral=True)

    @app_commands.command(name="stock_remove", description="(Désactivé) Le stock global est la somme des stocks admins.")
    async def stock_remove(self, interaction: discord.Interaction, montant: int):
        await interaction.response.send_message("❌ Le stock global est calculé automatiquement (somme des stocks admins). Utilisez les commandes *_admin.", ephemeral=True)


# =========================
# Setup
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(Stocks(bot))
