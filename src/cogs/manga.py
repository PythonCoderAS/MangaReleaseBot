from discord import Interaction
from discord.app_commands import Group, checks
from discord.app_commands.checks import bot_has_permissions, has_permissions
from discord.ext.commands import Cog, Context

from ..models import MangaEntry, Ping
from ..sources import BaseSource
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


class Manga(Cog):
    manga = Group(name="manga", description="Commands for managing manga updates.")

    def __init__(self, source_map: dict[str, BaseSource]):
        self.source_map = source_map

    @manga.command()
    async def add(self, interaction: Interaction, url: str, message_channel_first: bool = False, private: bool = False):
        """Add a manga for checking."""
        ctx = await Context.from_interaction(interaction)
        if private:
            if not ctx.channel.permissions_for(ctx.me).create_private_threads:
                return await ctx.send("I don't have permission to create private threads.")
            elif not ctx.channel.permissions_for(ctx.author).create_private_threads:
                return await ctx.send("You don't have permission to create private threads.")
        else:
            if not ctx.channel.permissions_for(ctx.me).create_public_threads:
                return await ctx.send("I don't have permission to create public threads.")
            elif not ctx.channel.permissions_for(ctx.author).create_public_threads:
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
                     if not k.startswith("_") and k not in ["guild_id", "channel_id","item_id", "source_id", "id"]},
                    guild_id=manga_obj.guild_id,
                    channel_id=manga_obj.channel_id, source_id=manga_obj.source_id, item_id=manga_obj.item_id)
                if created:
                    await ctx.send(f"Added a new entry for update checking (item ID {obj.id}).")
                ping_data = {"item": obj, "mention_id": manga_obj.creator_id, "is_role": False}
                ping_obj, ping_created = await Ping.get_or_create({}, **ping_data)
                if ping_created:
                    await ctx.send(f"Added you to ping list for new entries for update checking for item ID {obj.id}.")
                else:
                    await ctx.send(f"You are already pinged for new entries for update checking for item ID {obj.id}!")
                break
        else:
            await ctx.send(f"Could not find a source for {url}.")


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(Manga(bot.source_map))


