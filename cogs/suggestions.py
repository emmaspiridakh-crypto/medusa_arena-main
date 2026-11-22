from __future__ import annotations

import asyncio
import datetime as _dt
import logging
import re

import discord
from discord import ui
from discord.ext import commands

import config
from utils import storage

log = logging.getLogger("suggestions")

STORE_NAME = "suggestions"

LINK_RE = re.compile(r"(https?://|www\.|discord\.gg/|discord\.com/invite/)", re.IGNORECASE)

E_SUGGESTION = "<:name:1573470860696625283>"

GREEK_DAYS = ["Δευτέρα", "Τρίτη", "Τετάρτη", "Πέμπτη", "Παρασκευή", "Σάββατο", "Κυριακή"]
GREEK_MONTHS = [
    "", "Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου", "Ιουνίου",
    "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου", "Νοεμβρίου", "Δεκεμβρίου",
]


def _greek_date(dt: _dt.datetime) -> str:
    day_name = GREEK_DAYS[dt.weekday()]
    hour12 = dt.hour % 12 or 12
    period = "πμ" if dt.hour < 12 else "μμ"
    return f"{day_name}, {dt.day} {GREEK_MONTHS[dt.month]} {dt.year} {hour12:02d}:{dt.minute:02d} {period}"


def _sep() -> ui.Separator:
    return ui.Separator(visible=True, spacing=discord.SeparatorSpacing.small)


def _pe(emoji_id: int) -> discord.PartialEmoji:
    return discord.PartialEmoji(name="name", id=emoji_id)


def _parse_dt(value) -> _dt.datetime:
    if isinstance(value, str):
        try:
            return _dt.datetime.fromisoformat(value)
        except ValueError:
            pass
    return discord.utils.utcnow()


class Suggestions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._refresh_task: asyncio.Task | None = None

    def _build_view(
        self, *, author_id: int | None, text: str, upvotes: int, downvotes: int,
        msg_id: int, created_at: _dt.datetime, total: int,
    ) -> ui.LayoutView:
        author_str = f"<@{author_id}>" if author_id else "Άγνωστος"
        view = ui.LayoutView(timeout=None)
        view.add_item(
            ui.Container(
                _sep(),
                ui.Section(
                    ui.TextDisplay("# <:name:1573470860696625283> 〃 ***__NEW SUGGESTION__***"),
                    accessory=ui.Thumbnail(getattr(config, "SUGGESTIONS_THUMBNAIL_URL", "https://i.imgur.com/JcB78UI.png")),
                ),
                _sep(),
                ui.TextDisplay(
                    f"> <:name:1573453974063816876>〃 __**Submitted From:**__ {author_str}\n"
                    f"> <:name:1573362872363385003> 〃 __**Time:**__ {_greek_date(created_at)}"
                ),
                _sep(),
                ui.TextDisplay(f"<a:name:1572715696453058570> {text}"),
                _sep(),
                ui.ActionRow(
                    ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label=f"〃 Upvote ({upvotes})",
                        emoji=_pe(1573739991807430766),
                        custom_id=f"suggestion_up:{msg_id}",
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label=f"〃 Downvote ({downvotes})",
                        emoji=_pe(1573739995355807955),
                        custom_id=f"suggestion_down:{msg_id}",
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label="〃 Remove Vote",
                        emoji=_pe(1573868533220380863),
                        custom_id=f"suggestion_removevote:{msg_id}",
                    ),
                    ui.Button(
                        style=discord.ButtonStyle.secondary,
                        label=f"〃 Total Suggestions ({total})",
                        emoji=_pe(1573364435311923260),
                        custom_id="suggestion_total",
                        disabled=True,
                    ),
                ),
                _sep(),
                accent_colour=getattr(config, "SUGGESTIONS_PANEL_COLOUR", 0xA600FF),
            )
        )
        return view

    # ---------- Ενημέρωση του "Total Suggestions (N)" σε όλα τα suggestions ----------
    def _schedule_refresh(self):
        if self._refresh_task and not self._refresh_task.done():
            self._refresh_task.cancel()
        self._refresh_task = asyncio.create_task(self._refresh_all())

    async def _refresh_all(self):
        try:
            await asyncio.sleep(2)  # debounce: αν έρθουν πολλά μαζί, γίνεται ένα refresh
            channel = self.bot.get_channel(config.SUGGESTIONS_CHANNEL_ID)
            if channel is None:
                return

            removed_any = False
            for msg_id in list(storage.get_store(STORE_NAME).keys()):
                store = storage.get_store(STORE_NAME)
                info = store.get(msg_id)
                if not info:
                    continue
                view = self._build_view(
                    author_id=info.get("author_id"), text=info["text"],
                    upvotes=len(info["upvotes"]), downvotes=len(info["downvotes"]),
                    msg_id=int(msg_id), created_at=_parse_dt(info.get("created_at")),
                    total=len(store),
                )
                try:
                    await channel.get_partial_message(int(msg_id)).edit(view=view)
                except discord.NotFound:
                    # το μήνυμα διαγράφηκε (π.χ. όσο το bot ήταν offline) -> βγαίνει από το count
                    store = storage.get_store(STORE_NAME)
                    if store.pop(msg_id, None) is not None:
                        storage.save(STORE_NAME, store)
                        removed_any = True
                except discord.HTTPException:
                    pass
                await asyncio.sleep(1.2)  # rate limit

            if removed_any:
                self._schedule_refresh()
        except asyncio.CancelledError:
            raise

    # ---------- Διαγραφή suggestion ----------
    async def _forget_suggestions(self, message_ids: list[int]):
        store = storage.get_store(STORE_NAME)
        changed = False
        for mid in message_ids:
            if store.pop(str(mid), None) is not None:
                changed = True
        if changed:
            storage.save(STORE_NAME, store)
            self._schedule_refresh()

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        if payload.channel_id != config.SUGGESTIONS_CHANNEL_ID:
            return
        await self._forget_suggestions([payload.message_id])

    @commands.Cog.listener()
    async def on_raw_bulk_message_delete(self, payload: discord.RawBulkMessageDeleteEvent):
        if payload.channel_id != config.SUGGESTIONS_CHANNEL_ID:
            return
        await self._forget_suggestions(list(payload.message_ids))

    # ---------- Νέο suggestion ----------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        if message.channel.id != config.SUGGESTIONS_CHANNEL_ID:
            return

        content = message.content.strip()
        author = message.author

        has_mentions = bool(message.mentions) or bool(message.role_mentions) or message.mention_everyone
        has_link = bool(LINK_RE.search(content))

        if has_mentions or has_link:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            reason = "tags" if has_mentions and not has_link else "links" if has_link and not has_mentions else "tags ή links"
            try:
                warning = await message.channel.send(
                    f"{E_SUGGESTION} {author.mention} δεν επιτρέπονται **{reason}** μέσα στα suggestions."
                )
                await warning.delete(delay=6)
            except discord.HTTPException:
                pass
            return

        if not content:   # μόνο εικόνα/attachment, χωρίς κείμενο -> δεν γίνεται suggestion
            return

        created_at = discord.utils.utcnow()

        try:
            total_before = len(storage.get_store(STORE_NAME))
            temp_view = self._build_view(
                author_id=author.id, text=content, upvotes=0, downvotes=0,
                msg_id=0, created_at=created_at, total=total_before + 1,
            )
            sent = await message.channel.send(view=temp_view)
        except Exception:
            # αν αποτύχει η δημιουργία του panel, ΔΕΝ σβήνουμε το μήνυμα του χρήστη
            log.exception("[suggestions] Αποτυχία δημιουργίας suggestion panel")
            return

        try:
            await message.delete()
        except discord.HTTPException:
            pass

        try:
            store = storage.get_store(STORE_NAME)
            store[str(sent.id)] = {
                "author_id": author.id, "text": content, "upvotes": [], "downvotes": [],
                "created_at": created_at.isoformat(),
            }
            storage.save(STORE_NAME, store)

            real_view = self._build_view(
                author_id=author.id, text=content, upvotes=0, downvotes=0,
                msg_id=sent.id, created_at=created_at, total=len(store),
            )
            await sent.edit(view=real_view)
        except Exception:
            log.exception("[suggestions] Αποτυχία αποθήκευσης/ενημέρωσης suggestion")
            return

        # ενημέρωση του total και στα υπόλοιπα suggestions
        self._schedule_refresh()

    # ---------- Votes ----------
    async def _handle_vote(self, interaction: discord.Interaction, msg_id: int, upvote: bool | None):
        """upvote=True -> upvote toggle, False -> downvote toggle, None -> remove vote entirely."""
        store = storage.get_store(STORE_NAME)
        info = store.get(str(msg_id))
        if not info:
            await interaction.response.send_message("Δεν βρέθηκε αυτό το suggestion.", ephemeral=True)
            return

        uid = interaction.user.id
        ups, downs = set(info["upvotes"]), set(info["downvotes"])

        if upvote is None:
            ups.discard(uid)
            downs.discard(uid)
        elif upvote:
            if uid in ups:
                ups.discard(uid)
            else:
                ups.add(uid)
                downs.discard(uid)
        else:
            if uid in downs:
                downs.discard(uid)
            else:
                downs.add(uid)
                ups.discard(uid)

        info["upvotes"], info["downvotes"] = list(ups), list(downs)
        store[str(msg_id)] = info
        storage.save(STORE_NAME, store)

        new_view = self._build_view(
            author_id=info.get("author_id"), text=info["text"],
            upvotes=len(ups), downvotes=len(downs), msg_id=msg_id,
            created_at=_parse_dt(info.get("created_at")), total=len(store),
        )
        try:
            if interaction.response.is_done():
                await interaction.edit_original_response(view=new_view)
            else:
                await interaction.response.edit_message(view=new_view)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type != discord.InteractionType.component:
            return
        custom_id = interaction.data.get("custom_id", "")
        if custom_id.startswith("suggestion_up:"):
            await self._handle_vote(interaction, int(custom_id.split(":")[1]), upvote=True)
        elif custom_id.startswith("suggestion_down:"):
            await self._handle_vote(interaction, int(custom_id.split(":")[1]), upvote=False)
        elif custom_id.startswith("suggestion_removevote:"):
            await self._handle_vote(interaction, int(custom_id.split(":")[1]), upvote=None)


async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestions(bot))
