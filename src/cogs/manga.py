from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING, Union

from discord import Interaction, InteractionType, Role, TextChannel, User, Thread
from discord.app_commands import AppCommandThread, Group
from discord.ext.commands import Cog, Context
from tortoise.functions import Count

from ..models import MangaEntry, Ping, ThreadData
from ..sources import BaseSource

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


class Manga(Cog):
    manga = Group(name="manga", description="Commands for managing manga updates.")

    def __init__(self, source_map: dict[str, BaseSource]):
        self.source_map = source_map

    @manga.command()
    async def add(self, interaction: Interaction, url: str, message_channel_first: bool = False, private: bool =
    False, channel: Optional[TextChannel] = None):
        """Add a manga for checking."""
        ctx = await Context.from_interaction(interaction)
        if channel is None:
            channel = ctx.channel
        if private:
            if not channel.permissions_for(ctx.me).create_private_threads:
                return await ctx.send("I don't have permission to create private threads.")
            elif not channel.permissions_for(ctx.author).create_private_threads:
                return await ctx.send("You don't have permission to create private threads.")
        else:
            if not channel.permissions_for(ctx.me).create_public_threads:
                return await ctx.send("I don't have permission to create public threads.")
            elif not channel.permissions_for(ctx.author).create_public_threads:
                return await ctx.send("You don't have permission to create public threads.")
        if private and message_channel_first:
            return await ctx.send("A message cannot be sent first for private threads.")
        for name, source in self.source_map.items():
            if source.url_regex.search(url):
                await ctx.defer()
                manga_obj = await source.add_item(ctx, url)
                if manga_obj is None:
                    return
                manga_obj.guild_id = ctx.interaction.guild_id
                manga_obj.channel_id = ctx.interaction.channel_id
                manga_obj.creator_id = ctx.interaction.user.id
                manga_obj.source_id = name
                manga_obj.message_channel_first = message_channel_first
                manga_obj.private_thread = private
                obj, created = await MangaEntry.get_or_create(
                    {k: v for k, v in manga_obj.__dict__.items()
                     if not k.startswith("_") and k not in ["guild_id", "channel_id", "item_id", "source_id", "id"]},
                    guild_id=manga_obj.guild_id,
                    channel_id=manga_obj.channel_id, source_id=manga_obj.source_id, item_id=manga_obj.item_id)
                was_deleted = obj.deleted
                if was_deleted:
                    obj.deleted = None
                    obj.creator_id = manga_obj.creator_id
                    await obj.save()
                if created or was_deleted:
                    await ctx.send(f"Added a new entry for update checking (item ID {obj.id}).")
                return await self.subscribe_user(interaction, obj.id, ctx.author)
        else:
            await ctx.send(f"Could not find a source for {url}.")

    @manga.command()
    async def subscribe(self, interaction: Interaction, id: Optional[int] = None, thread: Optional[AppCommandThread] = None,
                        target: Optional[Union[User, Role]] = None):
        """Subscribe to a specific manga entry."""
        ctx = await Context.from_interaction(interaction)
        await ctx.defer()
        manga_entry = None
        if thread and id:
            obj = await ThreadData.get_or_none(thread_id=thread.id)
            if obj is None:
                return await ctx.send(
                    "This thread was not created by the bot. Please use this command in a thread created by the bot.")
            manga_entry = await MangaEntry.get_or_none(id=id)
            if manga_entry is None:
                return await ctx.send("This entry does not exist.")
            if (await obj.entry).id != id:
                return await ctx.send("Linked manga entry ID mistmatch. Please specify either `thread` or `id` but not both.")
        elif thread:
            obj = await ThreadData.get_or_none(thread_id=thread.id)
            if obj is None:
                return await ctx.send(
                    "This thread was not created by the bot. Please use this command in a thread created by the bot.")
            id = (await obj.entry).id
        if id is None:
            thread_id = ctx.channel.id
            obj = await ThreadData.get_or_none(thread_id=thread_id)
            if obj is None:
                return await ctx.send(
                    "This thread was not created by the bot. Please use this command in a thread created by the bot.")
            else:
                manga_entry = await obj.entry
                id = manga_entry.id
        if manga_entry is None:
            manga_entry = await MangaEntry.get_or_none(id=id)
            if manga_entry is None:
                return await ctx.send("Invalid item ID.")
        if target is None:
            target = ctx.author
        if target != ctx.author:
            if not ctx.channel.permissions_for(ctx.author).manage_threads and ctx.author.id != manga_entry.creator_id:
                return await ctx.send("You don't have permission to add other people or roles as targets.")
        await self.subscribe_user(interaction, id, target)

    @manga.command()
    async def unsubscribe(self, interaction: Interaction, id: Optional[int] = None, thread: Optional[AppCommandThread] = None,
                        target: Optional[Union[User, Role]] = None):
        """Unsubscribe from a specific manga entry."""
        ctx = await Context.from_interaction(interaction)
        await ctx.defer()
        manga_entry = None
        if thread and id:
            obj = await ThreadData.get_or_none(thread_id=thread.id)
            if obj is None:
                return await ctx.send(
                    "This thread was not created by the bot. Please use this command in a thread created by the bot.")
            manga_entry = await MangaEntry.get_or_none(id=id)
            if manga_entry is None:
                return await ctx.send("This entry does not exist.")
            if (await obj.entry).id != id:
                return await ctx.send("Linked manga entry ID mistmatch. Please specify either `thread` or `id` but not both.")
        elif thread:
            obj = await ThreadData.get_or_none(thread_id=thread.id)
            if obj is None:
                return await ctx.send(
                    "This thread was not created by the bot. Please use this command in a thread created by the bot.")
            id = (await obj.entry).id
        if id is None:
            thread_id = ctx.channel.id
            obj = await ThreadData.get_or_none(thread_id=thread_id)
            if obj is None:
                return await ctx.send(
                    "This thread was not created by the bot. Please use this command in a thread created by the bot.")
            else:
                manga_entry = await obj.entry
                id = manga_entry.id
        if manga_entry is None:
            manga_entry = await MangaEntry.get_or_none(id=id)
            if manga_entry is None:
                return await ctx.send("Invalid item ID.")
        if target is None:
            target = ctx.author
        if target != ctx.author:
            if not ctx.channel.permissions_for(ctx.author).manage_threads and ctx.author.id != manga_entry.creator_id:
                return await ctx.send("You don't have permission to remove other people or roles as targets.")
        await self.unsubscribe_user(interaction, id, target)

    async def subscribe_user(self, interaction: Interaction, item_id: int, target: Union[User, Role]):
        ping_data = {"item_id": item_id, "mention_id": target.id, "is_role": type(target) is Role}
        ping_obj, ping_created = await Ping.get_or_create({}, **ping_data)
        if ping_created:
            await interaction.followup.send(
                f"Added to ping list for new entries for update checking for item ID {item_id}.")
        else:
            if interaction.user.id == target.id:
                await interaction.followup.send(
                    f"You are already pinged for new entries for update checking for item ID {item_id}!")
            else:
                await interaction.followup.send(
                    f"They are already pinged for new entries for update checking for item ID {item_id}!")
        manga_entry = await ping_obj.item
        if manga_entry.deleted:
            manga_entry.deleted = None
            if not ping_data['is_role']:
                manga_entry.creator_id = interaction.user.id
            await manga_entry.save()
            await interaction.followup.send(f"Reactivated item {item_id} for update checking.")
            if not ping_data['is_role']:
                await interaction.followup.send(f"As the first non-role person to reactivate this manga entry, "
                                                f"you have been promoted to the creator of the entry.")

    async def unsubscribe_user(self, interaction: Interaction, item_id: int, target: Union[User, Role]):
        ping_data = {"item_id": item_id, "mention_id": interaction.user.id, "is_role": type(target) is Role}
        ping_obj = await Ping.get_or_none(**ping_data)
        if ping_obj:
            await ping_obj.delete()
            await interaction.followup.send(
                f"Removed you from the ping list for new entries for update checking for item ID {item_id}.")
        else:
            if interaction.user.id == target.id:
                await interaction.followup.send(
                    f"You were not being pinged for new entries for update checking for item ID {item_id}.")
            else:
                await interaction.followup.send(
                    f"They were not being pinged for new entries for update checking for item ID {item_id}.")
        manga_entry = await MangaEntry.get(id=item_id)
        other_pings, = await manga_entry.pings.all().annotate(count=Count("id")).values_list("count", flat=True)
        if other_pings == 0:
            manga_entry.deleted = datetime.now(tz=timezone.utc)
            await manga_entry.save()
            await interaction.followup.send(
                f"Deactivated item {item_id} for update checking. To reactivate, at least one other user or role must "
                f"be subscribed to pings.")

    async def process_button(self, interaction: Interaction):
        custom_id = interaction.data["custom_id"]
        if custom_id is None:
            return
        elif custom_id.startswith("subscribe_id_"):
            await interaction.response.defer()
            await self.subscribe_user(interaction, int(custom_id[13:]), interaction.user)
        elif custom_id.startswith("unsubscribe_id_"):
            await interaction.response.defer()
            await self.unsubscribe_user(interaction, custom_id[15:], interaction.user)

    @Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if interaction.type == InteractionType.component and "custom_id" in interaction.data:
            await self.process_button(interaction)


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(Manga(bot.source_map))
