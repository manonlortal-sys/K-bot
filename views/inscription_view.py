import discord


class InscriptionView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.sessions = {}

    # =========================
    # BUTTON START
    # =========================
    @discord.ui.button(
        label="🎮 Je participe",
        style=discord.ButtonStyle.success,
        custom_id="tournoi:start"
    )
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):

        if len(interaction.client.teams) >= 8:
            return await interaction.response.send_message("❌ Tournoi complet", ephemeral=True)

        self.sessions[interaction.user.id] = {
            "joueurs": None,
            "nom": None
        }

        await interaction.response.send_message(
            "👥 Envoie les 3 joueurs de ton équipe ici",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check, timeout=120)

        players = msg.content.split()[:3]

        self.sessions[interaction.user.id]["joueurs"] = players

        await self.ask_name(interaction)

    # =========================
    # STEP NAME
    # =========================
    async def ask_name(self, interaction):

        view = NameView(self)
        await interaction.followup.send(
            "🏷 Donne un nom d’équipe ou clique sur passer",
            view=view,
            ephemeral=True
        )

    # =========================
    # RECAP + FINAL
    # =========================
    async def show_recap(self, interaction, user_id):

        session = self.sessions[user_id]
        joueurs = session["joueurs"]
        nom = session["nom"]

        name = nom or "Équipe auto"

        text = []
        for i, p in enumerate(joueurs):
            if i == 0:
                text.append(f"👑 {p} (C)")
            else:
                text.append(f"👤 {p}")

        embed = discord.Embed(
            title="📋 Récap équipe",
            description="\n".join(text),
            color=0x9b59b6
        )

        embed.add_field(name="🏷 Nom", value=name, inline=False)

        view = ConfirmView(self, user_id)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# =========================
# NAME BUTTON VIEW
# =========================
class NameView(discord.ui.View):

    def __init__(self, parent):
        super().__init__(timeout=60)
        self.parent = parent

    @discord.ui.button(label="⏭ Passer", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        self.parent.sessions[interaction.user.id]["nom"] = None

        await self.parent.show_recap(interaction, interaction.user.id)

    @discord.ui.button(label="🏷 Valider nom", style=discord.ButtonStyle.primary)
    async def set_name(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "Envoie le nom de ton équipe",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check, timeout=120)

        self.parent.sessions[interaction.user.id]["nom"] = msg.content

        await self.parent.show_recap(interaction, interaction.user.id)


# =========================
# CONFIRM VIEW
# =========================
class ConfirmView(discord.ui.View):

    def __init__(self, parent, user_id):
        super().__init__(timeout=120)
        self.parent = parent
        self.user_id = user_id

    @discord.ui.button(label="🟢 Valider", style=discord.ButtonStyle.success)
    async def validate(self, interaction: discord.Interaction, button: discord.ui.Button):

        session = self.parent.sessions[self.user_id]

        team = {
            "capitaine": session["joueurs"][0],
            "joueurs": session["joueurs"],
            "nom": session["nom"]
        }

        interaction.client.teams.append(team)

        del self.parent.sessions[self.user_id]

        await interaction.response.send_message("✅ Équipe enregistrée", ephemeral=True)

        await interaction.client.update_teams_embed()

    @discord.ui.button(label="✏️ Modifier joueurs", style=discord.ButtonStyle.primary)
    async def edit_players(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message(
            "👥 Renvoie les 3 joueurs",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == self.user_id and msg.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check, timeout=120)

        self.parent.sessions[self.user_id]["joueurs"] = msg.content.split()[:3]

        await self.parent.show_recap(interaction, self.user_id)

    @discord.ui.button(label="🏷 Modifier nom", style=discord.ButtonStyle.secondary)
    async def edit_name(self, interaction: discord.Interaction, button: discord.ui.Button):

        await self.parent.ask_name(interaction)

    @discord.ui.button(label="🔴 Annuler", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.user_id in self.parent.sessions:
            del self.parent.sessions[self.user_id]

        await interaction.response.send_message("❌ Inscription annulée", ephemeral=True)
