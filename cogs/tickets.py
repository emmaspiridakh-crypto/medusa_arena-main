from __future__ import annotations

import asyncio

import discord
from discord import ui, app_commands
from discord.ext import commands

import config
from emojis import emoji
from utils import storage
from utils.permissions import has_roles

STORE_NAME = "tickets"
TRANSCRIPT_STORE = "ticket_transcripts"

PANEL_SELECT_ID = "ticket_select"

# ---------- Emojis του panel (hardcoded) ----------
E_TITLE = "<:name:1571835494172467282>"
E_INTRO = "<a:name:1572715696453058570>"
E_BULLET = "<:name:1573453240052486277>"
E_FOOTER = "<a:name:1573739983515418649>"

# ---------- Τύποι ticket ----------
# Category IDs και ρόλοι που βλέπουν τα tickets ορίζονται στο config.py
# (TICKET_CATEGORY_IDS / TICKET_VIEW_ROLE_IDS) με το ίδιο key.
TICKET_TYPES: dict[str, dict] = {
    "owner": {
        "label": "Owner",
        "emoji": "<:name:1573454146017824779>",
        "description": "Επικοινωνία με το Ownership",
    },
    "ban_appeal": {
        "label": "Ban Appeal",
        "emoji": "<:name:1573464177719115956>",
        "description": "Ανάκληση για κάποιο ban",
    },
    "staff_report": {
        "label": "Staff Report",
        "emoji": "<:name:1573457240701276180>",
        "description": "Αναφορά Staff",
    },
    "bug_report": {
        "label": "Bug Report",
        "emoji": "<:name:1573464800279924756>",
        "description": "Αναφορά κάποιου Bug",
    },
    "other": {
        "label": "Other",
        "emoji": "<:name:1572696314871943338>",
        "description": "Γενικό Support/Ερωτήσεις",
    },
    "criminal_support": {
        "label": "Criminal Support",
        "emoji": "<:name:1573837895838601336>",
        "description": "Support/Ερωτήσεις για criminals",
    },
}


def _ticket_types() -> dict[str, dict]:
    return {
        key: {
            **data,
            "category_id": config.TICKET_CATEGORY_IDS.get(key, 0),
            "view_roles": config.TICKET_VIEW_ROLE_IDS.get(key, []),
        }
        for key, data in TICKET_TYPES.items()
    }


def _sep() -> ui.Separator:
    return ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small)


def build_panel_view() -> ui.LayoutView:
    children: list = [
        _sep(),
        ui.MediaGallery(discord.MediaGalleryItem(media=config.TICKET_SUPPORT_BANNER_URL)),
        _sep(),
        ui.TextDisplay(f"## {E_TITLE} 〃 **__Medusa Arena - Ticket Center__**"),
        _sep(),
        ui.TextDisplay(
            f"{E_INTRO} Για την άμεση εξυπηρέτηση σας, επιλέξτε την κατηγορία που σας ενδιαφέρει "
            "και ανοίξτε ένα ticket ώστε επικοινωνήσετε μαζί μας."
        ),
        _sep(),
    ]
    for data in TICKET_TYPES.values():
        children.append(
            ui.TextDisplay(
                f"> **{E_BULLET}** {data['emoji']} 〃 **{data['label']}** — {data['description']}"
            )
        )
        children.append(_sep())

    select = ui.Select(
        custom_id=PANEL_SELECT_ID,
        placeholder="〃 Make A Selection",
        options=[
            discord.SelectOption(
                label=data["label"],
                value=key,
                emoji=discord.PartialEmoji.from_str(data["emoji"]),
            )
            for key, data in TICKET_TYPES.items()
        ],
    )
    children.append(ui.ActionRow(select))
    children.append(_sep())
    children.append(
        ui.TextDisplay(f"-# {E_FOOTER} 〃 **__Παρακαλούμε μην ανοίγετε ticket χωρίς λόγο__**")
    )
    children.append(_sep())

    view = ui.LayoutView(timeout=None)
    view.add_item(ui.Container(*children, accent_colour=config.TICKET_PANEL_COLOUR))
    return view


def build_ticket_view(opener: discord.abc.User, channel_id: int) -> ui.LayoutView:
    """Το panel που στέλνεται ΜΕΣΑ στο ticket channel."""
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            _sep(),
            ui.TextDisplay(f"## <a:name:1552723150515470406> 〃 __*Welcome {opener.mention}*__!"),
            _sep(),
            ui.Section(
                ui.TextDisplay(
                    "> <:name:1055592014630105128> Πες μας πως μπορούμε να σε βοηθήσουμε και σύντομα "
                    "θα επικοινωνήσουμε μαζί σου. Περιέγραψε το πρόβλημα σου όσο καλυτέρα μπορείς."
                ),
                accessory=ui.Thumbnail(config.TICKET_THUMBNAIL_URL),
            ),
            _sep(),
            ui.ActionRow(
                ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="〃 Close",
                    emoji=discord.PartialEmoji(name="name", id=1573455398344855643),
                    custom_id=f"ticket_close:{channel_id}",
                ),
                ui.Button(
                    style=discord.ButtonStyle.secondary,
                    label="〃 Ping User",
                    emoji=discord.PartialEmoji(name="name", id=1573455807058542682),
                    custom_id=f"ticket_ping:{channel_id}",
                ),
            ),
            _sep(),
            accent_colour=config.TICKET_PANEL_COLOUR,
        )
    )
    return view


def build_opened_view(channel_url: str) -> ui.LayoutView:
    """Το (ephemeral) μήνυμα που βλέπει ο χρήστης όταν ανοίξει ticket."""
    view = ui.LayoutView(timeout=None)
    view.add_item(
        ui.Container(
            _sep(),
            ui.TextDisplay("# <:name:1572728296993726585> 〃__***Your Tickent Has Opened.***__ "),
            _sep(),
            ui.TextDisplay("Πάτα το κουμπί παρακάτω για να πας στο ticket σου."),
            _sep(),
            ui.ActionRow(
                ui.Button(
                    style=discord.ButtonStyle.link,
                    label="〃 My ticket 〃",
                    emoji=discord.PartialEmoji(name="name", id=1572728296993726585),
                    url=channel_url,
                ),
            ),
            _sep(),
            ui.TextDisplay("> -  <a:name:1572715696453058570> Παρακαλούμε μην κάνεις spam."),
            _sep(),
            accent_colour=0xA600FF,
        )
    )
    return view


def _safe_name(text: str) -> str:
    text = text.lower().strip().replace(" ", "-")
    return "".join(c for c in text if c.isalnum() or c == "-")[:90]


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._opening: set[int] = set()   # χρήστες που αυτή τη στιγμή ανοίγουν ticket (anti double-click)

    async def create_ticket(self, interaction: discord.Interaction, ticket_key: str):
        # Reset του select menu (να μην μένει η επιλογή και να ξαναπατιέται η ίδια κατηγορία)
        try:
            await interaction.response.edit_message(view=build_panel_view())
        except discord.HTTPException:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)

        async def reply(text: str):
            await interaction.followup.send(text, ephemeral=True)

        data = _ticket_types().get(ticket_key)
        if not data:
            await reply("Άγνωστος τύπος ticket.")
            return

        guild = interaction.guild
        opener = interaction.user

        if opener.id in self._opening:
            await reply("Το ticket σου ανοίγει, περίμενε λίγο.")
            return

        self._opening.add(opener.id)
        try:
            await self._open_ticket(interaction, guild, opener, ticket_key, data, reply)
        finally:
            self._opening.discard(opener.id)

    async def _open_ticket(self, interaction, guild, opener, ticket_key, data, reply):
        store = storage.get_store(STORE_NAME)

        # Όριο ανοιχτών tickets ανά χρήστη (όλοι οι τύποι μαζί)
        open_channels = []
        for ch_id, info in store.items():
            if info.get("opener_id") != opener.id:
                continue
            channel = guild.get_channel(int(ch_id))
            if channel:
                open_channels.append(channel)
        if len(open_channels) >= config.MAX_OPEN_TICKETS_PER_USER:
            await reply(
                f"Έχεις ήδη ανοιχτό ticket: {open_channels[0].mention}\n"
                f"Μπορείς να έχεις μόνο {config.MAX_OPEN_TICKETS_PER_USER} ticket τη φορά."
            )
            return

        # Category (αν δεν έχει οριστεί/βρεθεί, πέφτει στο category του "other")
        category = guild.get_channel(data["category_id"]) if data["category_id"] else None
        if not isinstance(category, discord.CategoryChannel):
            category = guild.get_channel(config.TICKET_CATEGORY_IDS.get("other", 0))
        if not isinstance(category, discord.CategoryChannel):
            await reply("Δεν βρέθηκε το category.")
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            opener: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        for role_id in data["view_roles"]:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

        channel_name = f"{ticket_key.replace('_', '-')}-{_safe_name(opener.display_name)}"
        try:
            new_channel = await guild.create_text_channel(
                name=channel_name, category=category, overwrites=overwrites
            )
        except discord.HTTPException:
            await reply("Δεν μπόρεσε να δημιουργηθεί το ticket. Δοκίμασε ξανά ή ενημέρωσε το staff.")
            return

        store[str(new_channel.id)] = {
            "type": ticket_key,
            "opener_id": opener.id,
            "guild_id": guild.id,
        }
        storage.save(STORE_NAME, store)

        await new_channel.send(view=build_ticket_view(opener, new_channel.id))

        log_channel = guild.get_channel(config.LOG_TICKETS_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title=f"{emoji('tickets', 'ticket')} Ticket Opened",
                color=discord.Colour.green(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Τύπος", value=data["label"], inline=True)
            embed.add_field(name="Channel", value=new_channel.mention, inline=True)
            embed.add_field(name="Άνοιξε από", value=f"{opener.mention} (`{opener.id}`)", inline=False)
            await log_channel.send(embed=embed)

        await interaction.followup.send(view=build_opened_view(new_channel.jump_url), ephemeral=True)

    async def _build_transcript_text(self, channel: discord.TextChannel) -> str:
        lines = []
        try:
            async for msg in channel.history(limit=None, oldest_first=True):
                ts = msg.created_at.strftime("%d/%m %H:%M")
                author = msg.author.display_name
                content = msg.content or ""
                line = f"[{ts}] {author}: {content}"
                if msg.attachments:
                    for a in msg.attachments:
                        line += f" [📎 {a.filename}]"
                lines.append(line)
        except discord.HTTPException:
            pass

        return "\n".join(lines) if lines else "(δεν υπάρχουν μηνύματα)"

    def _add_transcript_fields(self, embed: discord.Embed, transcript: str, *, max_fields: int = 20, chunk_size: int = 1000) -> None:
        chunks = [transcript[i:i + chunk_size] for i in range(0, len(transcript), chunk_size)]
        truncated = len(chunks) > max_fields
        chunks = chunks[:max_fields]

        for i, chunk in enumerate(chunks, start=1):
            name = "Transcript" if len(chunks) == 1 else f"Transcript ({i}/{len(chunks)})"
            embed.add_field(name=name, value=f"```{chunk}```" if chunk.strip() else "```(κενό)```", inline=False)

        if truncated:
            embed.add_field(name=" Σημείωση", value="Το transcript ήταν πολύ μεγάλο και κόπηκε.", inline=False)

    async def handle_close(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Αυτό το ticket δεν υπάρχει πια.", ephemeral=True)
            return

        if interaction.user.id == info["opener_id"]:
            await interaction.response.send_message(
                "Δεν μπορείς να κλείσεις το δικό σου ticket.", ephemeral=True
            )
            return

        await interaction.response.send_message("Το ticket κλείνει σε 5 δευτερόλεπτα...", ephemeral=False)

        log_channel = interaction.guild.get_channel(config.LOG_TICKETS_CHANNEL_ID)
        if log_channel:
            transcript_text = await self._build_transcript_text(interaction.channel)

            transcripts = storage.get_store(TRANSCRIPT_STORE)
            transcripts[str(channel_id)] = {
                "text": transcript_text,
                "channel_name": interaction.channel.name,
                "opener_id": info["opener_id"],
                "closed_by": interaction.user.id,
            }
            storage.save(TRANSCRIPT_STORE, transcripts)

            ttypes = _ticket_types()
            type_label = ttypes.get(info["type"], {}).get("label", info["type"])
            embed = discord.Embed(
                title=f"{emoji('tickets', 'close')} Ticket Closed",
                color=discord.Colour.red(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Τύπος", value=type_label, inline=True)
            embed.add_field(name="Channel", value=f"`#{interaction.channel.name}`", inline=True)
            embed.add_field(name="Άνοιξε από", value=f"<@{info['opener_id']}>", inline=False)
            embed.add_field(name="Έκλεισε από", value=f"{interaction.user.mention} (`{interaction.user.id}`)", inline=False)

            transcript_btn = ui.Button(
                label="View Transcript", style=discord.ButtonStyle.secondary,
                custom_id=f"ticket_transcript:{channel_id}",
            )
            view = ui.View(timeout=None)
            view.add_item(transcript_btn)
            await log_channel.send(embed=embed, view=view)

        store.pop(str(channel_id), None)
        storage.save(STORE_NAME, store)
        await asyncio.sleep(5)
        channel = interaction.guild.get_channel(channel_id)
        if channel:
            await channel.delete(reason=f"Ticket closed by {interaction.user}")

    async def handle_ping_user(self, interaction: discord.Interaction, channel_id: int):
        store = storage.get_store(STORE_NAME)
        info = store.get(str(channel_id))
        if not info:
            await interaction.response.send_message("Tο ticket δεν υπάρχει πια.", ephemeral=True)
            return

        if not has_roles(interaction.user, config.STAFF_TEAM_ROLE_IDS):
            await interaction.response.send_message("Μόνο το staff team μπορεί να κάνει ping.", ephemeral=True)
            return

        if interaction.user.id == info["opener_id"]:
            await interaction.response.send_message("Δεν μπορείς να κάνεις ping τον εαυτό σου....", ephemeral=True)
            return

        opener = interaction.guild.get_member(info["opener_id"])
        await interaction.response.send_message(f"{opener.mention if opener else ''}", ephemeral=False)
        if opener:
            try:
                await opener.send(f"Έχεις ειδοποίηση στο ticket σου: {interaction.channel.mention}")
            except discord.Forbidden:
                pass

    async def handle_view_transcript(self, interaction: discord.Interaction, channel_id: int):
        transcripts = storage.get_store(TRANSCRIPT_STORE)
        record = transcripts.get(str(channel_id))
        if not record:
            await interaction.response.send_message("Δεν βρέθηκε transcript για αυτό το ticket.", ephemeral=True)
            return

        text = record["text"]
        header = f"**Transcript — #{record.get('channel_name', channel_id)}**\n"

        chunks = []
        current = ""
        for line in text.split("\n"):
            piece = line + "\n"
            if len(current) + len(piece) > 1900:
                chunks.append(current)
                current = ""
            current += piece
        if current:
            chunks.append(current)
        if not chunks:
            chunks = ["(δεν υπάρχουν μηνύματα)"]

        first = f"{header}```\n{chunks[0]}```"
        await interaction.response.send_message(first, ephemeral=True)
        for chunk in chunks[1:]:
            await interaction.followup.send(f"```\n{chunk}```", ephemeral=True)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")

        if custom_id == PANEL_SELECT_ID:
            value = interaction.data["values"][0]
            await self.create_ticket(interaction, value)
        elif custom_id.startswith("ticket_close:"):
            channel_id = int(custom_id.split(":")[1])
            await self.handle_close(interaction, channel_id)
        elif custom_id.startswith("ticket_ping:"):
            channel_id = int(custom_id.split(":")[1])
            await self.handle_ping_user(interaction, channel_id)
        elif custom_id.startswith("ticket_transcript:"):
            channel_id = int(custom_id.split(":")[1])
            await self.handle_view_transcript(interaction, channel_id)

    @app_commands.command(name="panel-support", description="Στέλνει το ticket panel")
    @app_commands.checks.has_any_role(config.OWNERSHIP_ROLE_ID, config.MANAGER_ROLE_ID, config.STAFF_ROLE_ID)
    async def panel_support(self, interaction: discord.Interaction):
        await interaction.channel.send(view=build_panel_view())
        await interaction.response.send_message("Στάλθηκε.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Tickets(bot))
