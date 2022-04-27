from asyncio import create_task, gather
from collections import defaultdict
from datetime import datetime
from typing import List, TYPE_CHECKING
from zoneinfo import ZoneInfo

from discord import ChannelType, Object, TextChannel
from discord.ext.commands import Cog
from discord.ext.tasks import loop

from ..models import MangaEntry, ThreadData
from ..sources import BaseSource
from ..sources.base import UpdateEntry
from ..views.thread_actions import ThreadActions

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot

UTC = ZoneInfo("UTC")


class UpdateChecker(Cog):
    @property
    def last_updated(self):
        return datetime.fromtimestamp(self.bot.config_manager.last_updated, tz=UTC)

    def __init__(self, bot: "MangaReleaseBot"):
        self.bot = bot

    async def cog_load(self):
        self.bot.config_manager.last_updated = (
            self.bot.config_manager.last_updated or 1650600000
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

    @loop(minutes=10, reconnect=False)
    async def update_check(self):
        await self.bot.wait_until_ready()
        print("Starting update check...")
        print(self.bot.config_manager.last_updated)
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
            print(guild_id, channel_id, guild)
            if guild:
                channel = guild.get_channel(channel_id)
                print(channel)
                if channel:
                    ids_to_check.append(channel_id)
        print("First round: ", ids_to_check)
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
                print(f"Second round for {source_id}:", by_item_id)
                tasks.append(
                    create_task(source.check_updates(self.last_updated, by_item_id))
                )
        entries: List[List[UpdateEntry]] = await gather(*tasks)
        print("Got entries: ", entries)
        entry_tasks = []
        for top_layer in entries:
            for entry in top_layer:
                print(f"Found update for {entry.entry.source_id}:{entry.entry.item_id}")
                entry_tasks.append(create_task(self.make_entry(entry)))
        await gather(*entry_tasks)
        self.bot.config_manager.last_updated = int(cur_time.timestamp())
        await self.bot.config_manager.save()
        print(self.bot.config_manager.last_updated)


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(UpdateChecker(bot))
