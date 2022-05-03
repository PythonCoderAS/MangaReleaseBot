from typing import TYPE_CHECKING

from discord import AllowedMentions, Interaction, TextChannel
from discord.app_commands import command, default_permissions, guild_only
from discord.ext.commands import Cog

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


class Utils(Cog):
    @command()
    @guild_only()
    @default_permissions(manage_threads=True)
    async def cleanup(
        self,
        interaction: Interaction,
        entire_server: bool = False,
        channel: TextChannel = None,
        item_id: int = None,
        thread: int = None,
        lock: bool = False,
    ):
        """Archives all threads made by the bot."""
        await interaction.response.defer()
        threads = []
        if entire_server:
            for channel in interaction.guild.text_channels:
                threads.extend(channel.threads)
            if item_id:
                # Not implemented yet
                # TODO: Implement this
                pass
        else:
            channel = channel or interaction.channel
            threads.extend(channel.threads)
        for thread in threads:
            await thread.send(
                f"Cleaning up thread due to cleanup command (executed by {interaction.user.mention}).",
                allowed_mentions=AllowedMentions.none(),
            )
            await thread.edit(archived=True, locked=False)
        await interaction.followup.send("Done.")


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(Utils())
