from datetime import datetime, timezone
from json import JSONDecodeError, loads
from typing import Optional, TYPE_CHECKING, Union

from discord import Attachment, InteractionType, Member, Role, TextChannel, User
from discord.app_commands import AppCommandThread, command, guild_only
from discord.ext.commands import Cog, GroupCog
from tortoise.functions import Count

from .._patched.types.discord import Context, Interaction
from ..errors.exceptions import BaseError, ErrorWithContext
from ..models import MangaEntry, Ping
from ..sources import BaseSource
from ..utils.manga import get_manga_entry, resolve_id_from_thread_or_id, save_config

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


@guild_only()
class Manga(
    GroupCog, group_name="manga", description="Commands for managing manga updates."
):
    def __init__(self, source_map: dict[str, BaseSource]):
        self.source_map = source_map

    @command()
    async def add(
        self,
        interaction: Interaction,
        url: str,
        message_channel_first: bool = False,
        private: bool = False,
        channel: Optional[TextChannel] = None,
    ):
        """Add a manga for checking."""
        ctx = await Context.from_interaction(interaction)
        if channel is None:
            channel = ctx.channel
        if private:
            if not channel.permissions_for(ctx.me).create_private_threads:
                raise ErrorWithContext(3, "Missing permission `create_private_threads`")
            elif not channel.permissions_for(ctx.author).create_private_threads:
                raise ErrorWithContext(1, "Missing permission `create_private_threads`")
        else:
            if not channel.permissions_for(ctx.me).create_public_threads:
                raise ErrorWithContext(3, "Missing permission `create_public_threads`")
            elif not channel.permissions_for(ctx.author).create_public_threads:
                raise ErrorWithContext(1, "Missing permission `create_public_threads`")
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
                    {
                        k: v
                        for k, v in manga_obj.__dict__.items()
                        if not k.startswith("_")
                        and k
                        not in ["guild_id", "channel_id", "item_id", "source_id", "id"]
                    },
                    guild_id=manga_obj.guild_id,
                    channel_id=manga_obj.channel_id,
                    source_id=manga_obj.source_id,
                    item_id=manga_obj.item_id,
                )
                was_deleted = obj.deleted
                if was_deleted:
                    obj.deleted = None
                    obj.creator_id = manga_obj.creator_id
                    await obj.save()
                if created or was_deleted:
                    await ctx.send(
                        f"Added a new entry for update checking (item ID {obj.id})."
                    )
                return await self.subscribe_user(interaction, obj.id, ctx.author)
        else:
            await ctx.send(f"Could not find a source for {url}.")

    @command()
    async def subscribe(
        self,
        interaction: Interaction,
        id: Optional[int] = None,
        thread: Optional[AppCommandThread] = None,
        target: Optional[Union[Member, Role]] = None,
    ):
        """Subscribe to a specific manga entry."""
        await interaction.response.defer()
        manga_id = await resolve_id_from_thread_or_id(id, thread or (interaction.channel if not id else None))
        if target is None:
            target = interaction.user
        if target.id != interaction.user.id:
            await get_manga_entry(manga_id, check_permissions_interaction=interaction)
        await self.subscribe_user(interaction, id, target)

    @command()
    async def unsubscribe(
        self,
        interaction: Interaction,
        id: Optional[int] = None,
        thread: Optional[AppCommandThread] = None,
        target: Optional[Union[Member, Role]] = None,
    ):
        """Unsubscribe from a specific manga entry."""
        await interaction.response.defer()
        manga_id = await resolve_id_from_thread_or_id(id, thread or (interaction.channel if not id else None))
        if target is None:
            target = interaction.user
        if target.id != interaction.user.id:
            await get_manga_entry(manga_id, check_permissions_interaction=interaction)
        await self.unsubscribe_user(interaction, id, target)

    @command()
    async def pause(
        self,
        interaction: Interaction,
        id: Optional[int] = None,
        thread: Optional[AppCommandThread] = None,
    ):
        """Pause a specific manga entry."""
        await interaction.response.defer()
        id = await resolve_id_from_thread_or_id(id, thread or (interaction.channel if not id else None))
        await self.pause_entry(interaction, id)

    @command()
    async def unpause(
        self,
        interaction: Interaction,
        id: Optional[int] = None,
        thread: Optional[AppCommandThread] = None,
    ):
        """Unpause a specific manga entry."""
        await interaction.response.defer()
        id = await resolve_id_from_thread_or_id(id, thread or (interaction.channel if not id else None))
        await self.unpause_entry(interaction, id)

    @command()
    async def customize(
        self,
        interaction: Interaction,
        id: Optional[int] = None,
        thread: Optional[AppCommandThread] = None,
        json: Optional[Attachment] = None,
    ):
        id = await resolve_id_from_thread_or_id(id, thread or (interaction.channel if not id else None))
        if not json:
            await self.customize_entry(interaction, id)
        else:
            data = await json.read()
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError:
                raise ErrorWithContext(7, "Not a valid text file.")
            try:
                json_data = loads(text)
            except JSONDecodeError:
                raise ErrorWithContext(7, "Contents are not valid JSON.")
            manga_entry = await get_manga_entry(
                id, check_permissions_interaction=interaction
            )
            await interaction.client.source_map[manga_entry.source_id].validate(
                manga_entry, json_data
            )
            await save_config(manga_entry, json_data, interaction)

    async def subscribe_user(
        self, interaction: Interaction, item_id: int, target: Union[User, Role]
    ):
        ping_data = {
            "item_id": item_id,
            "mention_id": target.id,
            "is_role": type(target) is Role,
        }
        ping_obj, ping_created = await Ping.get_or_create({}, **ping_data)
        if ping_created:
            await interaction.followup.send(
                f"Added to ping list for new entries for update checking for item ID {item_id}."
            )
        else:
            if interaction.user.id == target.id:
                await interaction.followup.send(
                    f"You are already pinged for new entries for update checking for item ID {item_id}!"
                )
            else:
                await interaction.followup.send(
                    f"They are already pinged for new entries for update checking for item ID {item_id}!"
                )
        manga_entry = await ping_obj.item
        if manga_entry.deleted:
            manga_entry.deleted = None
            if not ping_data["is_role"]:
                manga_entry.creator_id = interaction.user.id
            await manga_entry.save()
            await interaction.followup.send(
                f"Reactivated item {item_id} for update checking."
            )
            if not ping_data["is_role"]:
                await interaction.followup.send(
                    f"As the first non-role person to reactivate this manga entry, "
                    f"you have been promoted to the creator of the entry."
                )

    async def unsubscribe_user(
        self, interaction: Interaction, item_id: int, target: Union[User, Role]
    ):
        ping_data = {
            "item_id": item_id,
            "mention_id": interaction.user.id,
            "is_role": type(target) is Role,
        }
        ping_obj = await Ping.get_or_none(**ping_data)
        if ping_obj:
            await ping_obj.delete()
            await interaction.followup.send(
                f"Removed you from the ping list for new entries for update checking for item ID {item_id}."
            )
        else:
            if interaction.user.id == target.id:
                await interaction.followup.send(
                    f"You were not being pinged for new entries for update checking for item ID {item_id}."
                )
            else:
                await interaction.followup.send(
                    f"They were not being pinged for new entries for update checking for item ID {item_id}."
                )
        manga_entry = await MangaEntry.get(id=item_id)
        (other_pings,) = (
            await manga_entry.pings.all()
            .annotate(count=Count("id"))
            .values_list("count", flat=True)
        )
        if other_pings == 0:
            manga_entry.deleted = datetime.now(tz=timezone.utc)
            await manga_entry.save()
            await interaction.followup.send(
                f"Deactivated item {item_id} for update checking. To reactivate, at least one other user or role must "
                f"be subscribed to pings."
            )

    async def pause_entry(self, interaction: Interaction, item_id: int):
        manga_entry = await get_manga_entry(item_id, interaction)
        if manga_entry.paused:
            return await interaction.followup.send("This entry is already paused.")
        manga_entry.paused = datetime.now(tz=timezone.utc)
        await manga_entry.save()
        await interaction.followup.send(f"Paused entry {item_id}.")

    async def unpause_entry(self, interaction: Interaction, item_id: int):
        manga_entry = await get_manga_entry(item_id, interaction)
        if not manga_entry.paused:
            return await interaction.followup.send("This entry is not paused.")
        manga_entry.paused = None
        await manga_entry.save()
        await interaction.followup.send(f"Unpaused entry {item_id}.")

    async def customize_entry(self, interaction: Interaction, item_id: int):
        manga_entry = await get_manga_entry(item_id, interaction)
        modal = await interaction.client.source_map[manga_entry.source_id].customize(
            manga_entry
        )
        await interaction.response.send_modal(modal)

    async def process_button(self, interaction: Interaction):
        custom_id = interaction.data["custom_id"]
        if custom_id is None:
            return
        try:
            if custom_id.startswith("subscribe_id_"):
                await interaction.response.defer()
                await self.subscribe_user(
                    interaction, int(custom_id[13:]), interaction.user
                )
            elif custom_id.startswith("unsubscribe_id_"):
                await interaction.response.defer()
                await self.unsubscribe_user(
                    interaction, custom_id[15:], interaction.user
                )
            elif custom_id.startswith("pause_id_"):
                await interaction.response.defer()
                await self.pause_entry(interaction, custom_id[9:])
            elif custom_id.startswith("unpause_id_"):
                await interaction.response.defer()
                await self.unpause_entry(interaction, custom_id[11:])
            elif custom_id.startswith("customize_id_"):
                await self.customize_entry(interaction, custom_id[13:])
        except BaseError as exception:
            if interaction.response.is_done():
                await interaction.followup.send(exception.args[0])
            else:
                await interaction.response.send_message(exception.args[0])
        except Exception as exception:
            msg = f"Error: {exception}"
            if interaction.response.is_done():
                await interaction.followup.send(msg)
            else:
                await interaction.response.send_message(msg)

    @Cog.listener()
    async def on_interaction(self, interaction: Interaction):
        if (
            interaction.type == InteractionType.component
            and "custom_id" in interaction.data
        ):
            await self.process_button(interaction)


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(Manga(bot.source_map))
