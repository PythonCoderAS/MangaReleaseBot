from typing import Optional

from discord.abc import Snowflake

from .._patched.types.discord import Interaction
from ..errors.exceptions import Error, ErrorWithContext
from ..models import MangaEntry, ThreadData


async def get_manga_entry(id: int, check_permissions_interaction: Optional[Interaction] = None, target_id: Optional[
                                                                                                           int] = None)\
        -> \
        MangaEntry:
    manga_entry = await MangaEntry.get(id=id)
    if manga_entry is None:
        raise Error(2, entry_id=id)
    target_id = target_id or check_permissions_interaction.user.id
    if check_permissions_interaction is not None:
        member = check_permissions_interaction.guild.get_member(target_id)
        if (
                not check_permissions_interaction.channel.permissions_for(member).manage_threads
                and target_id != manga_entry.creator_id
        ):
            raise ErrorWithContext(1, "Cannot manage threads and is not item creator.")
    return manga_entry


async def resolve_id_from_thread_or_id(id: int, thread: Snowflake) -> int:
    if thread and id:
        raise Error(5)
    elif id:
        return id
    elif thread:
        obj = await ThreadData.get_or_none(thread_id=thread.id)
        if obj is None:
            raise Error(4, thread_id=thread.id)
        return obj.entry_id
    raise AssertionError("Should not reach this point.")
