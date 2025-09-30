# cogs/data.py
import os
import re
import math
import sqlite3
from pathlib import Path
from typing import Optional, Tuple, List

import discord
from discord.ext import commands
from discord import app_commands
from zoneinfo import ZoneInfo
from datetime import datetime

# =========================
# Config & Constantes
# =========================
ADMIN_ROLE_ID = int(os.getenv("ADMIN_ROLE_ID"))  # rôle admin (env Render)

# Canal où le bot poste les lignes /data
DATA_LOG_CHANNEL_ID = 1422520352138858506

# Canal où vit l'embed cumulatif
DATA_REPORT_CHANNEL_ID = 1420820345891590316

# DB (on réutilise le même fichier que stocks pour centraliser)
DB_PATH = Path("data/stocks.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

TZ_PARIS = ZoneInfo("Europe/Paris")

# Emojis
EMOJI_ACHAT = "💰"
EMOJI_VENTE = "⭐"
EMOJI_TOTALS = "🧮"
EMOJI_BENEF = "📈"
EMOJI_PERTE = "📉"
EMOJI_EGAL = "⚖️"

# Balise machine-lisible (recommandée, pas obligatoire)
# [[DATA|{achat|vente}|{M}|{TAUX}|{admin_id}]]
RE_TAG = re.compile(
    r"\[\[DATA\|(?P<kind>achat|vente)\|(?P<m>[-+]?\d+(?:[.,]\d+)?)\|(?P<rate>[-+]?\d+(?:[.,]\d+)?)\|(?P<admin_id>\d{5,})\]\]",
    re.IGNORECASE,
)

# Fallback parse du texte humain du journal (emoji optionnels)
# "💰 [Alice] a acheté 200 M au taux de 3,80 €/M — soit 760,00 €"
RE_HUMAN = re.compile(
    r"^\s*(?:[^\w\s])?\s*\[(?P<admin>[^\]]+)\]\s+a\s+(?P<action>acheté|vendu)\s+(?P<m>[-+]?\d+(?:[.,]\d+)?)\s*M\s+au\s+taux\s+de\s+(?P<rate>[-+]?\d+(?:[.,]\d+)?)\s*€/M",
    re.IGNORECASE,
)

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
    # Stocke uniquement la référence du message d'embed à éditer
    cur.execute("""
    CREATE TABLE IF NOT EXISTS data_report_meta (
        guild_id INTEGER PRIMARY KEY,
        msg_channel_id INTEGER,
        msg_id INTEGER,
        updated_at TEXT
    );
    """)
    conn.commit()
    conn.close()

def _now_paris_str() -> str:
    return datetime.now(TZ_PARIS).strftime("%d/%m/%Y %H:%M")

def _select_report_meta(guild_id: int) -> Tuple[Optional[int], Optional[int], Optional[str]]:
    conn = _db_connect()
    cur = conn.cursor()
    cur.execute("SELECT msg_channel_id, msg_id, updated_at FROM data_report_meta WHERE guild_id=?;", (guild_id,))
    row = cur.fetchone()
    conn.close()
    if row:
        return row[0], row[1], row[2]
    return None, None, None

def _upsert_report_meta(guild_id: int, msg_channel_id: int, msg_id: int) -> None:
    conn = _db_connect()
    cur = conn.cursor()
    now = _now_paris_str()
    cur.execute("""
        INSERT INTO data_report_meta(guild_id, msg_channel_id, msg_id, updated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(guild_id) DO UPDATE SET
            msg_channel_id=excluded.msg_channel_id,
            msg_id=excluded.msg_id,
            updated_at=excluded.updated_at;
    """, (guild_id, msg_channel_id, msg_id, now))
    conn.commit()
    conn.close()

# =========================
# Helpers formats & parse
# =========================
def _parse_decimal(value: str) -> float:
    """
    Accepte "12", "12.5", "12,5", "1 234,56".
    Renvoie float (attention : seulement utilisé pour affichage/convert rapide).
    """
    v = value.strip().replace(" ", "").replace("\u202f", "")
    v = v.replace(",", ".")
    return float(v)

def _fmt_euros(amount: float) -> str:
    # 1234.5 -> "1 234,50"
    s = f"{amount:,.2f}"
    s = s.replace(",", " ").replace(".", ",")
    return s

def _fmt_millions(amount: float) -> str:
    # 200 -> "200,00"
    s = f"{amount:,.2f}"
    s = s.replace(",", " ").replace(".", ",")
    return s

def _calc_euros(m_millions: float, rate_eur_per_m: float) -> float:
    # euros = M × (€ / M)
    return round(m_millions * rate_eur_per_m, 2)

def _is_admin_member(member: discord.Member) -> bool:
    role = member.guild.get_role(ADMIN_ROLE_ID) if member and member.guild else None
    return role in getattr(member, "roles", [])

# =========================
# Lecture journal & build tableaux
# =========================
class Line:
    __slots__ = ("kind", "admin", "admin_id", "m_millions", "rate", "euros")
    def __init__(self, kind: str, admin: str, admin_id: Optional[int], m_millions: float, rate: float):
        self.kind = kind  # 'achat' | 'vente'
        self.admin = admin
        self.admin_id = admin_id
        self.m_millions = m_millions
        self.rate = rate
        self.euros = _calc_euros(m_millions, rate)

async def _read_journal_lines(channel: discord.TextChannel) -> List[Line]:
    lines: List[Line] = []
    async for msg in channel.history(limit=None, oldest_first=True):
        if msg.author.bot is False:
            continue

        tag = None
        for ln in msg.content.splitlines():
            m = RE_TAG.search(ln)
            if m:
                tag = m
                break

        if tag:
            kind = tag.group("kind").lower()
            m_m = _parse_decimal(tag.group("m"))
            rate = _parse_decimal(tag.group("rate"))
            admin_id = int(tag.group("admin_id"))
            admin_name = None
            # Tenter de récupérer le nom depuis l'affichage au-dessus si possible
            hum = RE_HUMAN.search(msg.content)
            if hum:
                admin_name = hum.group("admin").strip()
            if not admin_name:
                admin_name = f"ID:{admin_id}"
            lines.append(Line(kind, admin_name, admin_id, m_m, rate))
            continue

        # Fallback : essayer de parser le texte humain
        hum = RE_HUMAN.search(msg.content)
        if hum:
            action = hum.group("action").lower()
            kind = "achat" if action == "acheté" else "vente"
            m_m = _parse_decimal(hum.group("m"))
            rate = _parse_decimal(hum.group("rate"))
            admin_name = hum.group("admin").strip()
            lines.append(Line(kind, admin_name, None, m_m, rate))

    return lines

def _build_tables(lines: List[Line]) -> Tuple[str, float, str, float, str, float]:
    """
    Construit les sections monospace pour Achats et Ventes + totaux + net.
    Retourne:
      (section_achats, total_achats_eur, section_ventes, total_ventes_eur, footer, net)
    """
    achats = [l for l in lines if l.kind == "achat"]
    ventes = [l for l in lines if l.kind == "vente"]

    def render_section(title_emoji: str, title_text: str, entries: List[Line]) -> Tuple[str, float]:
        header = f"{title_emoji} {title_text}\n"
        cols = "Admin           | M (millions) | Taux €/M | €\n"
        sep =   "----------------+--------------+----------+---------\n"
        body = ""
        total = 0.0
        for l in entries:
            admin = (l.admin or "—")[:15]
            mtxt = _fmt_millions(l.m_millions).rjust(12)
            rtxt = _fmt_millions(l.rate).rjust(8)  # réutilise format (virgule) pour taux
            etxt = _fmt_euros(l.euros).rjust(7)
            body += f"{admin:<15} | {mtxt} | {rtxt} | {etxt}\n"
            total += l.euros
        total_txt = _fmt_euros(total)
        total_line = f"{EMOJI_TOTALS} Total {title_text.lower()} (€){' ' * 23}= {total_txt}\n"
        section = "```\n" + header + cols + sep + (body if body else "(aucune entrée)\n") + total_line + "```"
        return section, total

    sec_achats, tot_achats = render_section(EMOJI_ACHAT, "ACHATS", achats)
    sec_ventes, tot_ventes = render_section(EMOJI_VENTE, "VENTES", ventes)

    net = round(tot_ventes - tot_achats, 2)
    if math.isclose(net, 0.0, abs_tol=0.005):
        footer = f"**{EMOJI_EGAL} Équilibre = {_fmt_euros(0)} €**"
    elif net > 0:
        footer = f"**{EMOJI_BENEF} Bénéfice net = +{_fmt_euros(net)} €**"
    else:
        footer = f"**{EMOJI_PERTE} Perte nette = −{_fmt_euros(abs(net))} €**"

    return sec_achats, tot_achats, sec_ventes, tot_ventes, footer, net

def _make_embed(sec_achats: str, sec_ventes: str, footer: str) -> discord.Embed:
    title = "📊 Bilan cumulatif — Achats & Ventes"
    intro = "Données cumulatives issues du journal. Montants en millions (M). Taux en €/M."
    e = discord.Embed(title=title, description=intro, color=discord.Color.orange())
    # Discord limite ~4096 caractères en description. On met les sections en fields.
    # Si trop long, on tronque proprement.
    def clamp(s: str, maxlen: int = 1000) -> str:
        return (s[: maxlen - 1] + "…") if len(s) > maxlen else s

    e.add_field(name="Achats", value=clamp(sec_achats), inline=False)
    e.add_field(name="Ventes", value=clamp(sec_ventes), inline=False)
    e.add_field(name="\u200b", value=footer, inline=False)
    e.set_footer(text=f"Dernière mise à jour : {_now_paris_str()} (heure de Paris)")
    return e

# =========================
# Cog
# =========================
class DataCog(commands.Cog):
    """Gestion /data (journal) + embed cumulatif (achats/ventes) reconstruit depuis le journal."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        # Init DB table
        await self.bot.loop.run_in_executor(None, _db_init)
        # Au chargement du cog : s'assurer que l'embed existe et reflète le journal
        # (si le bot redémarre, on reconstruit)
        for guild in self.bot.guilds:
            try:
                await self._ensure_report_up_to_date(guild)
            except Exception:
                # On évite de planter au démarrage d'autres serveurs
                pass

    # -------------------------
    # Commandes
    # -------------------------
    @app_commands.command(name="data", description="Enregistrer une ligne Achat/Vente dans le journal.")
    @app_commands.describe(
        type="Type d'opération",
        montant_m="Montant en millions (décimal autorisé)",
        taux="Taux en €/million (décimal, virgule ou point)",
    )
    @app_commands.choices(type=[
        app_commands.Choice(name="Achat", value="achat"),
        app_commands.Choice(name="Vente", value="vente"),
    ])
    async def data(self, interaction: discord.Interaction, type: app_commands.Choice[str], montant_m: str, taux: str):
        # Permissions
        if not isinstance(interaction.user, discord.Member) or not _is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return

        guild = interaction.guild
        if guild is None:
            return

        # Parse entrées
        try:
            m_val = _parse_decimal(montant_m)  # millions
            r_val = _parse_decimal(taux)       # €/M
            if m_val <= 0 or r_val <= 0:
                raise ValueError
        except Exception:
            await interaction.response.send_message(
                "❌ Saisie invalide : vérifie le montant (en millions) et le taux (€/M).",
                ephemeral=True
            )
            return

        euros = _calc_euros(m_val, r_val)
        m_txt = _fmt_millions(m_val)
        r_txt = _fmt_millions(r_val)
        e_txt = _fmt_euros(euros)

        # Post dans le canal journal (sans ping)
        log_ch = guild.get_channel(DATA_LOG_CHANNEL_ID)
        if not isinstance(log_ch, discord.TextChannel):
            await interaction.response.send_message("Canal journal introuvable.", ephemeral=True)
            return

        emoji = EMOJI_ACHAT if type.value == "achat" else EMOJI_VENTE
        human_line = f"{emoji} [{interaction.user.display_name}] a {'acheté' if type.value=='achat' else 'vendu'} {m_txt} M au taux de {r_txt} €/M — soit {e_txt} €"
        tag_line = f"[[DATA|{type.value}|{m_val}|{r_val}|{interaction.user.id}]]"
        await log_ch.send(human_line + "\n" + tag_line)

        # Met à jour / crée l'embed cumulatif
        await self._ensure_report_up_to_date(guild)

        await interaction.response.send_message("✅ Donnée enregistrée dans le journal. Le bilan a été mis à jour.", ephemeral=True)

    @app_commands.command(name="data_ini", description="Réinitialiser le bilan à zéro (sans relecture du journal).")
    async def data_ini(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not _is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return
        guild = interaction.guild
        if guild is None:
            return

        # Embed vide
        empty_achats = "```\n💰 ACHATS\nAdmin           | M (millions) | Taux €/M | €\n----------------+--------------+----------+---------\n(aucune entrée)\n🧮 Total achats (€)                       = 0,00\n```"
        empty_ventes = "```\n⭐ VENTES\nAdmin           | M (millions) | Taux €/M | €\n----------------+--------------+----------+---------\n(aucune entrée)\n🧮 Total ventes (€)                       = 0,00\n```"
        footer = f"**{EMOJI_EGAL} Équilibre = 0,00 €**"
        embed = _make_embed(empty_achats, empty_ventes, footer)

        # Assurer existence du message d'embed dans le canal report
        report_ch = guild.get_channel(DATA_REPORT_CHANNEL_ID)
        if not isinstance(report_ch, discord.TextChannel):
            await interaction.response.send_message("Canal rapport introuvable.", ephemeral=True)
            return

        ch_id, msg_id, _ = await self.bot.loop.run_in_executor(None, _select_report_meta, guild.id)
        msg = None
        if ch_id and msg_id:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    msg = await ch.fetch_message(msg_id)
                except discord.NotFound:
                    msg = None

        if msg:
            await msg.edit(embed=embed)
        else:
            new_msg = await report_ch.send(embed=embed)
            await self.bot.loop.run_in_executor(None, _upsert_report_meta, guild.id, report_ch.id, new_msg.id)

        await interaction.response.send_message("🧹 Bilan réinitialisé. Les tableaux et totaux sont à 0,00 € (journal non relu).", ephemeral=True)

    @app_commands.command(name="data_rebuild", description="Relecture complète du journal et reconstruction du bilan.")
    async def data_rebuild(self, interaction: discord.Interaction):
        if not isinstance(interaction.user, discord.Member) or not _is_admin_member(interaction.user):
            await interaction.response.send_message("Réservé aux administrateurs.", ephemeral=True)
            return
        guild = interaction.guild
        if guild is None:
            return

        await self._ensure_report_up_to_date(guild, force_recreate=False)
        await interaction.response.send_message("🔄 Bilan reconstruit à partir de l’historique du journal.", ephemeral=True)

    # -------------------------
    # Coeur : créer/éditer l'embed à partir du journal
    # -------------------------
    async def _ensure_report_up_to_date(self, guild: discord.Guild, force_recreate: bool = False):
        # 1) Lire le journal
        log_ch = guild.get_channel(DATA_LOG_CHANNEL_ID)
        if not isinstance(log_ch, discord.TextChannel):
            return

        lines = await _read_journal_lines(log_ch)

        # 2) Construire sections & embed
        sec_achats, _, sec_ventes, _, footer, _ = _build_tables(lines)
        embed = _make_embed(sec_achats, sec_ventes, footer)

        # 3) Récupérer/créer le message d'embed
        report_ch = guild.get_channel(DATA_REPORT_CHANNEL_ID)
        if not isinstance(report_ch, discord.TextChannel):
            return

        ch_id, msg_id, _ = await self.bot.loop.run_in_executor(None, _select_report_meta, guild.id)
        msg = None
        if ch_id and msg_id and not force_recreate:
            ch = guild.get_channel(ch_id)
            if isinstance(ch, discord.TextChannel):
                try:
                    msg = await ch.fetch_message(msg_id)
                except discord.NotFound:
                    msg = None

        if msg is None:
            # Créer un nouveau message
            new_msg = await report_ch.send(embed=embed)
            await self.bot.loop.run_in_executor(None, _upsert_report_meta, guild.id, report_ch.id, new_msg.id)
        else:
            # Éditer l'existant
            await msg.edit(embed=embed)

# =========================
# Setup
# =========================
async def setup(bot: commands.Bot):
    await bot.add_cog(DataCog(bot))
