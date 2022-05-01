from typing import Optional

from aiohttp import ClientSession
from discord import Intents, Interaction
from discord.app_commands import AppCommandError, CommandInvokeError as AppCommandInvokeError
from discord.ext.commands import Bot, CommandError, CommandInvokeError as ExtCommandInvokeError, CommandNotFound, \
    Context, when_mentioned
from hondana import Client

from ._patched import discord as patched_discord
from .config import bot_token, mangadex_password, mangadex_username
from .config_manager import ConfigManager
from .errors.exceptions import BaseError
from .orm import init
from .sources import make_source_map


class MangaReleaseBot(Bot):
    def __init__(self):
        self.config_manager: Optional[ConfigManager] = None
        self.session: Optional[ClientSession] = None
        self.hondana: Optional[Client] = None
        intents = Intents.default()
        intents.members = True
        super().__init__(when_mentioned, intents=intents)
        self.source_map = make_source_map(self)
        patched_discord.bot = self  # Singleton

        @self.tree.error
        async def on_error(interaction: Interaction, exception: AppCommandError):
            if isinstance(exception, AppCommandInvokeError):
                if isinstance(exception.original, BaseError):
                    if interaction.response.is_done():
                        await interaction.followup.send(exception.original.args[0])
                    else:
                        await interaction.response.send_message(exception.original.args[0])
            elif isinstance(exception, CommandNotFound):
                return
            else:
                if interaction.response.is_done():
                    await interaction.followup.send(f"Error: {exception}")
                else:
                    await interaction.response.send_message(f"Error: {exception}")

    async def setup_hook(self) -> None:
        await init()
        self.config_manager = await ConfigManager.get()
        self.session = ClientSession()
        self.hondana = Client(
            session=self.session, username=mangadex_username, password=mangadex_password
        )
        await self.load_extension("jishaku")
        await self.load_extension("..cogs.manga", package=__name__)
        await self.load_extension("..cogs.update_check", package=__name__)
        await self.load_extension("..cogs.utils", package=__name__)

    async def close(self) -> None:
        await self.config_manager.save()
        await self.session.close()
        return await super().close()

    async def on_command_error(self, context: Context, exception: CommandError, /):
        if isinstance(exception, ExtCommandInvokeError):
            if isinstance(exception.original, BaseError):
                return await context.send(exception.original.args[0])
        elif isinstance(exception, CommandNotFound):
            return
        else:
            await context.send(f"Error: {exception}")




def main():
    MangaReleaseBot().run(bot_token)
