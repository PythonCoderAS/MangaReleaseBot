import logging
from asyncio import CancelledError, Lock, create_task, gather, shield, wait_for
from collections import defaultdict
from datetime import datetime
from typing import List, TYPE_CHECKING
from zoneinfo import ZoneInfo

from discord import ChannelType, Object, TextChannel, Thread
from discord.ext.commands import Cog, Context, command, is_owner
from discord.ext.tasks import loop

from ..models import MangaEntry, ThreadData
from ..sources import BaseSource
from ..sources.base import UpdateEntry
from ..views.thread_actions import ThreadActions

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot

UTC = ZoneInfo("UTC")
logger = logging.getLogger(__name__)


class UpdateChecker(Cog):
    @property
    def last_updated(self):
        return datetime.fromtimestamp(self.bot.config_manager.last_updated, tz=UTC)

    def __init__(self, bot: "MangaReleaseBot"):
        self.bot = bot
        self.locks = defaultdict(Lock)

    async def cog_load(self):
        self.bot.config_manager.last_updated = getattr(
            self.bot.config_manager, "last_updated", 1650600000
        )
        self.update_check.start()

    async def cog_unload(self):
        self.update_check.cancel()

    async def make_entry(self, entry: UpdateEntry):
        manga_entry = entry.entry
        channel: TextChannel = self.bot.get_guild(manga_entry.guild_id).get_channel(
            manga_entry.channel_id
        )
        if manga_entry.message_channel_first:
            msg = await channel.send(content=entry.message, embed=entry.embed)
            thread = await msg.create_thread(
                name=entry.thread_title, reason="Making thread for update."
            )
        else:
            thread = await channel.create_thread(
                name=entry.thread_title,
                reason="Making thread for update.",
                type=ChannelType.public_thread,
            )
            await thread.send(content=entry.message, embed=entry.embed)
        pings = await manga_entry.pings.all()
        for ping in pings:
            if ping.is_role:
                await thread.send(f"Adding role: <@&{ping.mention_id}>")
            else:
                await thread.add_user(Object(ping.mention_id))
        action_message = await thread.send(
            f"Manga Entry ID: **{manga_entry.id}**\n\n**__Thread Actions__**",
            view=ThreadActions(manga_entry.id),
        )
        if thread.permissions_for(
            self.bot.get_guild(manga_entry.guild_id).me
        ).manage_messages:
            await action_message.pin()
        thread_data = ThreadData(thread_id=thread.id, entry=manga_entry)
        await thread_data.save()

    async def archive_thread(self, thread: Thread):
        # Precondition: Thread is owned by bot.
        await thread.send(
            "Archiving thread prematurely to make space for more threads."
        )
        await thread.edit(
            archived=True,
            locked=False,
            reason="Archiving thread to make space for more threads.",
        )

    async def process_guild(self, tasks: List[UpdateEntry]):
        # Precondition: len(tasks) > 0
        first = tasks[0]
        guild = self.bot.get_guild(first.entry.guild_id)
        async with self.locks[guild.id]:
            active_threads = sum(
                len(channel.threads) for channel in guild.text_channels
            )
            if active_threads + len(tasks) > 1000:  # Max 1k threads per guild
                cleaned_requires = active_threads + len(tasks) - 1000
                logger.debug(
                    "Too many threads, attempting to clean up %s threads",
                    cleaned_requires,
                )
                my_threads = []
                for channel in guild.text_channels:
                    for thread in channel.threads:
                        if thread.owner_id == self.bot.user.id:
                            my_threads.append(thread)
                my_threads.sort(
                    key=lambda thread: (thread.last_message_id or 0, thread.created_at)
                )
                # If there is no last message, it's probably an old thread, and so we aggressively target these first.
                # Has to be `or 0` because you cannot compare an int and None.
                if len(my_threads) < cleaned_requires:
                    logger.debug(
                        "Not enough threads to clean up, cleaning %s threads and skipping %s threads.",
                        len(my_threads),
                        cleaned_requires - len(my_threads),
                    )
                    worked_tasks = tasks[: len(my_threads)]
                    threads_to_clean = my_threads
                    await gather(
                        *[self.archive_thread(thread) for thread in threads_to_clean]
                    )
                    await gather(*[self.make_entry(task) for task in worked_tasks])
                    return
                else:
                    logger.debug(
                        "Found enough threads to clean up, cleaning up %s threads",
                        cleaned_requires,
                    )
                    threads_to_clean = my_threads[:cleaned_requires]
                    for thread in threads_to_clean:
                        await self.archive_thread(thread)
            await gather(*[self.make_entry(task) for task in tasks])

    @loop(minutes=10, reconnect=False)
    async def update_check(self):
        await self.bot.wait_until_ready()
        logger.debug("Starting update check (last checked at %s)", self.last_updated)
        cur_time = datetime.now(UTC)
        first_filter_round = (
            await MangaEntry.all()
            .distinct()
            .filter(deleted=None, paused=None)
            .values_list("guild_id", "channel_id")
        )
        ids_to_check = []
        for guild_id, channel_id in first_filter_round:
            guild = self.bot.get_guild(guild_id)
            if guild:
                channel = guild.get_channel(channel_id)
                if channel:
                    ids_to_check.append(channel_id)
        second_filter_round: List[str] = (
            await MangaEntry.all()
            .distinct()
            .filter(deleted=None, paused=None)
            .values_list("source_id", flat=True)
        )
        tasks = []
        for source_id in second_filter_round:
            source: BaseSource = self.bot.source_map.get(source_id, None)
            if source:
                items = await MangaEntry.filter(
                    source_id=source_id,
                    channel_id__in=ids_to_check,
                    deleted=None,
                    paused=None,
                ).all()
                by_item_id = defaultdict(list)
                for item in items:
                    by_item_id[item.item_id].append(item)
                logger.debug("Providing %s to %s", items, type(source).__name__)
                tasks.append(
                    create_task(source.check_updates(self.last_updated, by_item_id))
                )
            else:
                logger.debug("No source object found for %s", source_id)
        entries: List[List[UpdateEntry]] = await gather(*tasks)  # type: ignore
        logger.debug("Got entries: %s", entries)
        entry_tasks: dict[str, list[UpdateEntry]] = defaultdict(list)
        for top_layer in entries:
            for entry in top_layer:
                logger.debug("Found entry: %s", entry)
                entry_tasks[entry.entry.guild_id].append(entry)
        try:
            await wait_for(
                shield(
                    gather(
                        *[
                            create_task(self.process_guild(item))
                            for item in entry_tasks.values()
                        ]
                    )
                ),
                60 * 9,
            )
        except (CancelledError, TimeoutError):
            logger.debug("Stopped waiting for the update check.")
        self.bot.config_manager.last_updated = int(cur_time.timestamp())
        await self.bot.config_manager.save()

    @command()
    @is_owner()
    async def stop(self, ctx: Context):
        """Safely stop the update checker after its next iteration."""
        self.update_check.stop()
        await ctx.send("Queued update checker for stopping.")


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(UpdateChecker(bot))
