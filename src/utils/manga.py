from typing import Optional

from ..errors.exceptions import Error, ErrorWithContext
from ..models import MangaEntry
from .._patched.types.discord import Interaction


async def get_manga_entry(id: int,  check_permissions_interaction: Optional[Interaction]) -> MangaEntry:
    manga_entry = await MangaEntry.get(id=id)
    if manga_entry is None:
        raise Error(2, id=id)
    if check_permissions_interaction is not None:
        member = check_permissions_interaction.guild.get_member(check_permissions_interaction.user.id)
        if (
                not check_permissions_interaction.channel.permissions_for(member).manage_threads
                and check_permissions_interaction.user.id != manga_entry.creator_id
        ):
            raise ErrorWithContext(1, "Cannot manage threads and is not item creator.")
    return manga_entry
