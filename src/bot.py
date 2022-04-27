from typing import Optional

from aiohttp import ClientSession
from discord import Intents
from discord.ext.commands import Bot, CommandError, Context, when_mentioned
from hondana import Client

from .config import bot_token, mangadex_password, mangadex_username
from .config_manager import ConfigManager
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

    async def close(self) -> None:
        await self.config_manager.save()
        await self.session.close()
        return await super().close()

    async def on_command_error(self, context: Context, exception: CommandError, /):
        await context.send(f"Error: {exception}")


def main():
    MangaReleaseBot().run(bot_token)
