from typing import TYPE_CHECKING

from discord import Interaction as DiscordInteraction
from discord.ext.commands import Context as DiscordContext

if TYPE_CHECKING:
    from ...bot import MangaReleaseBot


class Interaction(DiscordInteraction):
    @property
    def client(self) -> "MangaReleaseBot":
        return super().client  # type: ignore # Ignored because we know what subclass the client is.


class Context(DiscordContext["MangaReleaseBot"]):
    pass
