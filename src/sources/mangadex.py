import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import (
    Any,
    AsyncGenerator,
    Callable,
    ClassVar,
    Coroutine,
    Dict,
    List,
    Optional,
    Sequence,
    TypedDict,
)

from hondana import Chapter, Client, ContentRating, NotFound
from hondana.enums import Order
from hondana.query import ChapterIncludes, FeedOrderQuery

from .base import BaseModal, BaseSource, UpdateEntry
from ..models import MangaEntry

includes = ChapterIncludes()
order = FeedOrderQuery(created_at=Order.ascending)
content_ratings = [
    ContentRating.safe,
    ContentRating.suggestive,
    ContentRating.erotica,
    ContentRating.pornographic,
]


def get_resource_method(
        hondana_client: Client, resource: str
) -> Callable[[str], Coroutine[Any, Any, Any]]:
    if resource in ("title", "manga"):
        return hondana_client.get_manga
    elif resource in ("author", "artist"):
        return hondana_client.get_author
    elif resource == "group":
        return hondana_client.get_scanlation_group
    elif resource == "user":
        return hondana_client.get_user
    elif resource == "list":
        return hondana_client.get_custom_list
    else:
        raise ValueError(f"Unknown resource: {resource}")


class MangaDexCustomizations(TypedDict, total=True):
    languages: List[str]
    whitelisted_groups: List[str]
    blacklisted_groups: List[str]
    whitelisted_users: List[str]
    blacklisted_users: List[str]
    whitelisted_content_ratings: List[str]
    blacklisted_content_ratings: List[str]
    whitelisted_tags: List[str]
    blacklisted_tags: List[str]
    external_links: bool


class MangaDex(BaseSource):

    source_name = "MangaDex"
    url_regex = re.compile(
        r"^https?://mangadex\.org/(title|user|group|manga|author)/([0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{"
        r"4}\b-[0-9a-fA-F]{4}\b-[0-9a-fA-F]{12}|\*)"
    )

    default_customizations: ClassVar[MangaDexCustomizations] = {
        "languages": ["en"],
        "whitelisted_groups": [],
        "blacklisted_groups": [],
        "whitelisted_users": [],
        "blacklisted_users": [],
        "whitelisted_content_ratings": [],
        "blacklisted_content_ratings": [],
        "whitelisted_tags": [],
        "blacklisted_tags": [],
        "external_links": False,
    }

    async def customize(self, entry: MangaEntry) -> BaseModal:
        pass

    async def get_id(self, url: str) -> Optional[str]:
        match = self.url_regex.match(url)
        if not match:
            return None
        resource_type = match.group(1)
        if resource_type == "title":
            resource_type = "manga"
        resource_id = match.group(2)
        if resource_id == "*":
            return "*:*"
        try:
            await get_resource_method(self.bot.hondana, resource_type)(resource_id)
        except NotFound:
            return None
        return f"{resource_type}:{resource_id}"

    def filter_chapter_entry(self, chapter: Chapter, entry: MangaEntry) -> bool:
        customizations: Optional[MangaDexCustomizations] = entry.extra_config
        if not customizations:
            return True
        if not customizations["external_links"] and chapter.external_url:
            return False
        if (
                customizations["languages"]
                and chapter.translated_language not in customizations["languages"]
                and "*" not in customizations["languages"]
        ):
            return False
        if customizations["whitelisted_groups"]:
            if chapter.scanlator_groups:
                for group in chapter.scanlator_groups:
                    if group in customizations["whitelisted_groups"]:
                        break
                else:
                    return False
            elif "no group" in customizations["whitelisted_groups"]:
                pass
            else:
                return False
        if customizations["blacklisted_groups"]:
            if chapter.scanlator_groups:
                for group in chapter.scanlator_groups:
                    if group.id in customizations["blacklisted_groups"]:
                        return False
            elif "no group" in customizations["blacklisted_groups"]:
                return False
        resource_type, sep, resource_id = entry.item_id.partition(":")
        if resource_type != "user":
            if (
                    customizations["whitelisted_users"]
                    and chapter.uploader.id not in customizations["whitelisted_users"]
            ):
                return False
            if (
                    customizations["blacklisted_users"]
                    and chapter.uploader.id in customizations["blacklisted_users"]
            ):
                return False
        if resource_type != "manga":
            if (
                    customizations["whitelisted_content_ratings"]
                    and chapter.manga.content_rating
                    not in customizations["whitelisted_content_ratings"]
            ):
                return False
            if (
                    customizations["blacklisted_content_ratings"]
                    and chapter.manga.content_rating
                    in customizations["blacklisted_content_ratings"]
            ):
                return False
            if customizations["whitelisted_tags"] and chapter.manga.tags:
                for tag in chapter.manga.tags:
                    if tag.id in customizations["whitelisted_tags"]:
                        pass
                return False
            if customizations["blacklisted_tags"] and chapter.manga.tags:
                for tag in chapter.manga.tags:
                    if tag.id in customizations["blacklisted_tags"]:
                        return False
        return True

    async def all_chapters(
            self, start_time: Optional[datetime], **kwargs
    ) -> AsyncGenerator[Chapter, None]:
        while True:
            data = await self.bot.hondana.chapter_list(
                **kwargs,
                limit=100,
                order=order,
                includes=includes,
                include_future_updates=False,
                content_rating=content_ratings,
                created_at_since=start_time,
            )
            for item in data.items:
                yield item
            if len(data.items) == 0:
                return
            else:
                start_time = data.items[-1].created_at + timedelta(seconds=1)

    async def check_updates(
            self, last_update: datetime, data: Dict[str, Sequence[MangaEntry]]
    ) -> List[UpdateEntry]:
        resource_types: Dict[str, Dict[str, Sequence[MangaEntry]]] = defaultdict(
            lambda: defaultdict(list)
        )
        entries = []
        for key, value in data.items():
            resource_type, sep, resource_id = key.partition(":")
            if resource_id == "*":
                resource_type = "*"
            resource_types[resource_type][resource_id] = value
        async for chapter in self.all_chapters(last_update):
            title = chapter.manga.title
            suffix = f" Chapter {chapter.chapter or chapter.title or 'Oneshot'}"
            suffix_len = len(suffix)
            if len(title) + suffix_len > 100:  # Max thread title length is 100.
                max_len = 100 - suffix_len
                title = title[:max_len - 1] + "…"
            title += suffix
            if "*" in resource_types:
                for entry in resource_types["*"]["*"]:
                    if self.filter_chapter_entry(chapter, entry):
                        entries.append(UpdateEntry(entry, title, message=chapter.url))
            if chapter.manga:
                if "manga" in resource_types:
                    for entry in resource_types["manga"][chapter.manga.id]:
                        if self.filter_chapter_entry(chapter, entry):
                            entries.append(
                                UpdateEntry(entry, title, message=chapter.url)
                            )
                if "author" in resource_types and (
                        *chapter.manga.authors,
                        *chapter.manga.artists,
                ):
                    for author in set(
                            item.id
                            for item in (*chapter.manga.authors, *chapter.manga.artists)
                    ):
                        for entry in resource_types["author"][author]:
                            if self.filter_chapter_entry(chapter, entry):
                                entries.append(
                                    UpdateEntry(entry, title, message=chapter.url)
                                )
            if "user" in resource_types and chapter.uploader:
                for entry in resource_types["user"][chapter.uploader.id]:
                    if self.filter_chapter_entry(chapter, entry):
                        entries.append(UpdateEntry(entry, title, message=chapter.url))
            if "group" in resource_types and chapter.scanlator_groups:
                for group in chapter.scanlator_groups:
                    for entry in resource_types["group"][group.id]:
                        if self.filter_chapter_entry(chapter, entry):
                            entries.append(
                                UpdateEntry(entry, title, message=chapter.url)
                            )
        return entries
