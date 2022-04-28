from typing import TYPE_CHECKING

from .base import BaseSource
from .guya import Danke, Guya, Hachirumi, MahouShoujoBu
from .mangadex import MangaDex

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


def make_source_map(bot: "MangaReleaseBot") -> dict[str, BaseSource]:
    return {
        key: value(bot)
        for key, value in globals().items()
        if isinstance(value, type)
        and issubclass(value, BaseSource)
        and value is not BaseSource
    }
