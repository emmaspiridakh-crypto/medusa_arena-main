from __future__ import annotations

import asyncio
import logging
import time

import discord
from discord import ui
from discord.ext import commands

import config
from emojis import emoji
from utils import storage
from utils.components import build_base_container, add_separator, add_text

log = logging.getLogger("support_voice")

STORE_NAME = "temp_voice"


class SupportVoice(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._cooldowns: dict[int, float] = {}   # user_id -> monotonic time του τελευταίου ανοίγματος
        self._creating: set[int] = set()         # χρήστες που αυτή τη στιγμή τους φτιάχνεται voice
        self._temp_ids: set[int] = set()         # temp voices στη μνήμη (δουλεύει και αν αποτύχει το storage)
        self._swept = False

    # ---------- helpers ----------
    @staticmethod
    def _hubs() -> dict[int, tuple[str, dict]]:
        """hub_channel_id -> (type_key, type_data) μόνο για όσα έχουν οριστεί."""
        return {
            data["hub_channel_id"]: (key, data)
            for key, data in config.TEMP_VOICE_TYPES.items()
            if data.get("hub_channel_id")
        }

    def _build_view(
        self, member: discord.Member, ping_role: discord.Role | None,
        label: str, voice: discord.VoiceChannel,
    ) -> ui.LayoutView:
        ping_value = ping_role.mention if ping_role else "—"

        container = build_base_container(title=f"{emoji('notifier', 'bell')} {label} Notifier")
        if ping_role:
            add_text(container, ping_role.mention)
        add_separator(container)
        add_text(container, "**User Details:**")
        add_text(
            container,
            f"{emoji('notifier', 'hash')} **Username:** `{member.name}`\n"
            f"{emoji('notifier', 'hash')} **Mention:** {member.mention}\n"
            f"{emoji('notifier', 'person')} **ID:** `{member.id}`\n"
            f"{emoji('notifier', 'hash')} **Voice:** {voice.mention}\n"
            f"{emoji('notifier', 'bell')} **Ping:** {ping_value}\n"
            f"{emoji('notifier', 'clock')} **Time:** {discord.utils.format_dt(discord.utils.utcnow(), style='F')}",
        )

        view = ui.LayoutView(timeout=None)
        view.add_item(container)
        return view

    def _remaining_cooldown(self, user_id: int) -> int:
        last = self._cooldowns.get(user_id)
        if last is None:
            return 0
        left = config.TEMP_VOICE_COOLDOWN_SECONDS - (time.monotonic() - last)
        return int(left) + 1 if left > 0 else 0

    def _purge_cooldowns(self):
        now = time.monotonic()
        for uid in [u for u, t in self._cooldowns.items() if now - t > config.TEMP_VOICE_COOLDOWN_SECONDS]:
            self._cooldowns.pop(uid, None)

    def _register(self, channel_id: int, record: dict):
        self._temp_ids.add(channel_id)
        try:
            store = storage.get_store(STORE_NAME)
            store[str(channel_id)] = record
            storage.save(STORE_NAME, store)
        except Exception:
            log.exception("[support_voice] Αποτυχία αποθήκευσης temp voice (συνεχίζω με μνήμη)")

    def _is_temp(self, channel_id: int) -> bool:
        if channel_id in self._temp_ids:
            return True
        try:
            return str(channel_id) in storage.get_store(STORE_NAME)
        except Exception:
            return False

    def _forget(self, channel_id: int):
        self._temp_ids.discard(channel_id)
        try:
            store = storage.get_store(STORE_NAME)
            if store.pop(str(channel_id), None) is not None:
                storage.save(STORE_NAME, store)
        except Exception:
            log.exception("[support_voice] Αποτυχία διαγραφής από storage")

    async def _delete_temp(self, channel: discord.VoiceChannel, reason: str = "Temp voice άδειασε"):
        try:
            await channel.delete(reason=reason)
        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            log.error(f"[support_voice] Αποτυχία διαγραφής #{channel}: {e}")
            return
        self._forget(channel.id)

    # ---------- δημιουργία temp voice ----------
    async def _handle_hub_join(
        self, member: discord.Member, hub: discord.VoiceChannel, key: str, data: dict,
    ):
        guild = member.guild

        if member.id in self._creating:
            return

        left = self._remaining_cooldown(member.id)
        if left:
            # cooldown -> τον βγάζουμε από το hub για να μην γίνεται spam
            try:
                await member.move_to(None, reason="Temp voice cooldown")
            except discord.HTTPException:
                pass
            try:
                await member.send(f"Περίμενε {left} δευτερόλεπτα πριν ανοίξεις νέο voice.")
            except discord.HTTPException:
                pass
            return

        self._creating.add(member.id)
        try:
            ping_role = guild.get_role(data.get("ping_role_id") or 0)
            if not ping_role:
                log.warning(f"[support_voice] ({key}) Δεν βρέθηκε ρόλος με ID={data.get('ping_role_id')}.")

            overwrites: dict = {
                guild.default_role: discord.PermissionOverwrite(view_channel=False, connect=False),
                guild.me: discord.PermissionOverwrite(view_channel=True, connect=True),
                member: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True),
            }
            role_ids = {config.OWNERSHIP_ROLE_ID}
            if ping_role:
                role_ids.add(ping_role.id)
            for rid in role_ids:
                role = guild.get_role(rid)
                if role:
                    overwrites[role] = discord.PermissionOverwrite(
                        view_channel=True, connect=True, speak=True
                    )

            category = guild.get_channel(data.get("category_id") or 0)
            if not isinstance(category, discord.CategoryChannel):
                if data.get("category_id"):
                    log.warning(f"[support_voice] ({key}) Δεν βρέθηκε category με ID={data.get('category_id')}")
                category = hub.category

            name = f"{data['label']}-{member.display_name}"[:100]
            try:
                voice = await guild.create_voice_channel(
                    name=name, category=category, overwrites=overwrites,
                    reason=f"Temp voice ({key}) για {member}",
                )
            except discord.Forbidden as e:
                log.error(
                    f"[support_voice] ({key}) Forbidden στη δημιουργία voice: {e}. "
                    f"Το bot χρειάζεται Manage Channels, Manage Roles (Permissions), Move Members και "
                    f"Connect/View Channel στο category ID={category.id if category else None}."
                )
                return
            except discord.HTTPException as e:
                log.error(f"[support_voice] ({key}) Αποτυχία δημιουργίας voice για {member}: {e}")
                return

            self._register(voice.id, {"type": key, "owner_id": member.id, "guild_id": guild.id})

            try:
                await member.move_to(voice, reason="Temp voice")
            except discord.Forbidden as e:
                log.error(f"[support_voice] ({key}) Forbidden στο move_to: {e}. Λείπει το Move Members.")
                await self._delete_temp(voice, reason="Αποτυχία μετακίνησης")
                return
            except discord.HTTPException as e:
                # ο χρήστης έφυγε από το hub πριν προλάβουμε να τον μετακινήσουμε
                log.info(f"[support_voice] Δεν μετακινήθηκε ο {member}: {e}")
                await self._delete_temp(voice, reason="Ο χρήστης δεν μετακινήθηκε")
                return

            self._cooldowns[member.id] = time.monotonic()
            self._purge_cooldowns()

            notify_channel = guild.get_channel(data.get("notify_channel_id") or 0)
            if not notify_channel:
                log.warning(
                    f"[support_voice] ({key}) Δεν βρέθηκε notify channel με ID={data.get('notify_channel_id')}."
                )
                return

            try:
                await notify_channel.send(
                    view=self._build_view(member, ping_role, data["label"], voice),
                    allowed_mentions=discord.AllowedMentions(roles=True),
                )
                log.info(f"[support_voice] Στάλθηκε notify ({key}) για {member}.")
            except discord.Forbidden:
                log.error(f"[support_voice] Forbidden: δεν μπορώ να στείλω στο #{notify_channel}.")
            except discord.HTTPException as e:
                log.error(f"[support_voice] HTTPException κατά την αποστολή notify: {e}")
        finally:
            self._creating.discard(member.id)

    # ---------- listeners ----------
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        try:
            await self._on_voice_state_update(member, before, after)
        except Exception:
            log.exception(f"[support_voice] Απρόσμενο σφάλμα για {member}")

    async def _on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return
        if before.channel == after.channel:   # mute/deafen κλπ
            return

        if after.channel:
            log.info(
                f"[support_voice] {member} μπήκε σε voice {after.channel.name} "
                f"(ID={after.channel.id}) - hub? {after.channel.id in self._hubs()}"
            )

        # 1) Διαγραφή temp voice όταν αδειάσει
        if before.channel:
            if self._is_temp(before.channel.id) and not before.channel.members:
                await self._delete_temp(before.channel)

        # 2) Μπήκε σε hub -> δημιουργία temp voice + notify
        if after.channel:
            hub_info = self._hubs().get(after.channel.id)
            if hub_info:
                key, data = hub_info
                await self._handle_hub_join(member, after.channel, key, data)

    @commands.Cog.listener()
    async def on_ready(self):
        """Καθαρισμός temp voices που έμειναν (π.χ. αν το bot ήταν offline)."""
        if self._swept:
            return
        self._swept = True

        # Διαγνωστικά config
        seen: dict[int, str] = {}
        for key, data in config.TEMP_VOICE_TYPES.items():
            hub_id = data.get("hub_channel_id")
            if not hub_id:
                log.warning(f"[support_voice] ({key}) απενεργοποιημένο: hub_channel_id=0")
                continue
            if hub_id in seen:
                log.error(
                    f"[support_voice] ΛΑΘΟΣ CONFIG: οι τύποι '{seen[hub_id]}' και '{key}' έχουν το ίδιο "
                    f"hub_channel_id={hub_id}. Μόνο ο ένας θα δουλεύει - βάλε διαφορετικό hub σε κάθε τύπο."
                )
            seen[hub_id] = key
            hub = self.bot.get_channel(hub_id)
            if hub is None:
                log.error(f"[support_voice] ({key}) Δεν βρέθηκε hub channel ID={hub_id} (λάθος ID ή το bot δεν το βλέπει).")
            elif not isinstance(hub, discord.VoiceChannel):
                log.error(f"[support_voice] ({key}) Το ID={hub_id} είναι {type(hub).__name__}, όχι VoiceChannel.")
            else:
                perms = hub.guild.me.guild_permissions
                missing = [
                    n for n in ("manage_channels", "manage_roles", "move_members")
                    if not getattr(perms, n)
                ]
                if missing and not perms.administrator:
                    log.error(f"[support_voice] ({key}) Λείπουν δικαιώματα από το bot: {', '.join(missing)}")
                else:
                    log.info(f"[support_voice] ({key}) OK: hub=#{hub.name} ({hub_id})")
            if not self.bot.get_channel(data.get("notify_channel_id") or 0):
                log.error(f"[support_voice] ({key}) Δεν βρέθηκε notify channel ID={data.get('notify_channel_id')}.")
        try:
            store = storage.get_store(STORE_NAME)
        except Exception:
            log.exception("[support_voice] Αποτυχία ανάγνωσης storage στο sweep")
            return
        self._temp_ids.update(int(k) for k in store.keys())
        for ch_id in list(store.keys()):
            channel = self.bot.get_channel(int(ch_id))
            if channel is None:
                self._forget(int(ch_id))
            elif isinstance(channel, discord.VoiceChannel) and not channel.members:
                await self._delete_temp(channel, reason="Temp voice έμεινε άδειο")
                await asyncio.sleep(0.5)


async def setup(bot: commands.Bot):
    await bot.add_cog(SupportVoice(bot))
