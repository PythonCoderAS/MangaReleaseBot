from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Pattern, Sequence, TYPE_CHECKING

from discord import Embed
from discord.ext.commands import Context
from tortoise.functions import Count

from ..models import MangaEntry

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


@dataclass(frozen=True)
class UpdateEntry:
    entry: MangaEntry
    thread_title: str
    embed: Optional[Embed] = None
    message: Optional[str] = None


class BaseSource(ABC):
    """
    Base class for sources.
    """

    source_name: str
    url_regex: Pattern

    def __init__(self, bot: "MangaReleaseBot"):
        self.bot = bot

    @abstractmethod
    async def get_id(self, url: str) -> Optional[str]:
        """Get the ID of the item from the URL. Return None if not found."""
        raise NotImplementedError

    async def add_item(self, ctx: Context, url: str) -> Optional[MangaEntry]:
        """Add an item to be notified of in the future."""
        item_id = await self.get_id(url)
        if item_id is None:
            await ctx.send(f"Valid manga not found for the {self.source_name} source.")
            return
        return MangaEntry(item_id=item_id)

    async def remove_item(self, ctx: Context, entry: MangaEntry):
        """Remove an item from being notified."""
        items = await entry.pings.all().annotate(count=Count("id")).group_by("is_role").values("is_role", "count")
        role = user = 0
        for item in items:
            if item["is_role"]:
                role = item["count"]
            else:
                user = item["count"]
        message = f"Removed release notification ID {entry.id} (with {role} roles and {user} users)."
        await entry.delete()
        await ctx.send(message)

    @abstractmethod
    async def check_updates(self, last_update: datetime, data: Dict[str, Sequence[MangaEntry]]) -> List[UpdateEntry]:
        """Check for updates and return a list of UpdateEntry objects."""
        raise NotImplementedError
