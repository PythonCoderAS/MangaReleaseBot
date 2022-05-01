from typing import TYPE_CHECKING

from discord import AllowedMentions, Interaction, TextChannel
from discord.app_commands import command
from discord.ext.commands import Cog, Context, command as ext_command

from ..errors.exceptions import ErrorWithContext

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


class Utils(Cog):
    @command()
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
        if not interaction.user.resolved_permissions.manage_threads:
            raise ErrorWithContext(1, "Lacking permission `manage_threads`.")
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

    @ext_command()
    async def stop(self, ctx: Context["MangaReleaseBot"]):
        """Stops the bot."""
        await ctx.bot.close()


async def setup(bot: "MangaReleaseBot"):
    await bot.add_cog(Utils())