import discord


class InscriptionView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)
        self.sessions = {}

    @discord.ui.button(
        label="🎮 Je participe",
        style=discord.ButtonStyle.success,
        custom_id="tournoi:start"
    )
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):

        if len(interaction.client.teams) >= 8:
            return await interaction.response.send_message("❌ Tournoi complet", ephemeral=True)

        self.sessions[interaction.user.id] = {"joueurs": None, "nom": None}

        await interaction.response.send_message(
            "👥 Envoie les 3 joueurs ici",
            ephemeral=True
        )

        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check, timeout=120)

        self.sessions[interaction.user.id]["joueurs"] = msg.content.split()[:3]

        await self.ask_name(interaction)

    async def ask_name(self, interaction):

        view = NameView(self)

        await interaction.followup.send(
            "🏷 Nom d’équipe ou passer",
            view=view,
            ephemeral=True
        )

    async def show_recap(self, interaction, user_id):

        session = self.sessions[user_id]

        joueurs = session["joueurs"]
        nom = session["nom"]

        name = nom or "Équipe auto"

        lines = []
        for i, p in enumerate(joueurs):
            if i == 0:
                lines.append(f"👑 {p} (C)")
            else:
                lines.append(f"👤 {p}")

        embed = discord.Embed(
            title="📋 Récap équipe",
            description="\n".join(lines),
            color=0x9b59b6
        )

        embed.add_field(name="🏷 Nom", value=name, inline=False)

        view = ConfirmView(self, user_id)

        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


class NameView(discord.ui.View):

    def __init__(self, parent):
        super().__init__(timeout=60)
        self.parent = parent

    @discord.ui.button(label="⏭ Passer", style=discord.ButtonStyle.secondary)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.defer(ephemeral=True)

        self.parent.sessions[interaction.user.id]["nom"] = None

        await self.parent.show_recap(interaction, interaction.user.id)

    @discord.ui.button(label="🏷 Inscrire nom", style=discord.ButtonStyle.primary)
    async def set_name(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message("Envoie le nom", ephemeral=True)

        def check(msg):
            return msg.author.id == interaction.user.id and msg.channel.id == interaction.channel.id

        msg = await interaction.client.wait_for("message", check=check, timeout=120)

        self.parent.sessions[interaction.user.id]["nom"] = msg.content

        await self.parent.show_recap(interaction, interaction.user.id)


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
            "nom": session["nom"],
            "paid": False
        }

        interaction.client.teams.append(team)

        del self.parent.sessions[self.user_id]

        await interaction.response.send_message("✅ Équipe enregistrée", ephemeral=True)

        # =========================
        # MESSAGE SALON DISCUSSION
        # =========================
        channel = await interaction.client.fetch_channel(1492796809351925831)

        embed = discord.Embed(
            title="🏆 Inscription finalisée",
            color=0x9b59b6
        )

        embed.add_field(name="🏷 Équipe", value=team["nom"] or "Équipe auto", inline=False)
        embed.add_field(name="👑 Capitaine", value=team["joueurs"][0], inline=False)
        embed.add_field(name="👥 Joueurs", value="\n".join(team["joueurs"]), inline=False)
        embed.add_field(name="💳 Statut", value="⏳ En attente de paiement", inline=False)

        view = PaymentView(team)

        await channel.send(
            content="<@&1489520344330145884>",
            embed=embed,
            view=view
        )

        await interaction.client.update_teams_embed()

    @discord.ui.button(label="✏️ Modifier joueurs", style=discord.ButtonStyle.primary)
    async def edit_players(self, interaction: discord.Interaction, button: discord.ui.Button):

        await interaction.response.send_message("👥 Renvoie les 3 joueurs", ephemeral=True)

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

        await interaction.response.send_message("❌ Annulé", ephemeral=True)


class PaymentView(discord.ui.View):

    def __init__(self, team):
        super().__init__(timeout=None)
        self.team = team

    @discord.ui.button(label="Payé ✅", style=discord.ButtonStyle.success)
    async def paid(self, interaction: discord.Interaction, button: discord.ui.Button):

        role_id = 1489520344330145884

        if role_id not in [r.id for r in interaction.user.roles]:
            return await interaction.response.send_message(
                "❌ réservé aux organisateurs",
                ephemeral=True
            )

        self.team["paid"] = True

        await interaction.response.send_message("✅ Paiement validé", ephemeral=True)

        await interaction.client.update_teams_embed()