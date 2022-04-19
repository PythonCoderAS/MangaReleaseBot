from .guya import Guya
from .base import BaseSource
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


def make_source_map(bot: "MangaReleaseBot") -> dict[str, BaseSource]:
    return {key: value(bot) for key, value in globals().items()
            if isinstance(value, type)
            and issubclass(value, BaseSource)
            and value is not BaseSource}
