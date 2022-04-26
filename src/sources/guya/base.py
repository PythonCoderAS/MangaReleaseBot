import re
from datetime import datetime
from typing import Dict, List, Optional, Sequence

from discord import Embed
from guyamoe_api_types import AllSeries, Chapter, Series

from ..base import BaseSource, UpdateEntry
from ...models import MangaEntry


def get_preferred_chapter_data(chapter_data: Chapter, preferred_groups: list[str]) -> tuple[List[str], int, str]:
    """Gets the pages and release time of the preferred group for a chapter."""
    groups = chapter_data['groups']
    release_date = chapter_data['release_date']
    for group in preferred_groups:
        if group in release_date:
            return groups[group], release_date[group], group
    # If this line errors with a key error, it means that there are no groups
    # for the chapter, which should *not* happen.
    first_idx = sorted(groups.keys())[0]
    return groups[first_idx], release_date[first_idx], first_idx


class Guya(BaseSource):

    source_name = 'guya.moe'
    url_regex = re.compile(r'^https://guya.(?:cubari.)?moe/read/manga/([\w-]+|\*)', re.IGNORECASE)

    base_endpoint = 'https://guya.moe/api'
    website_endpoint = 'https://guya.moe'

    async def get_id(self, url: str) -> Optional[str]:
        slug = self.url_regex.search(url).group(1)
        if slug == '*':
            return slug
        async with self.bot.session.get(f'{self.base_endpoint}/series/{slug}') as resp:
            if resp.status == 404:
                return
            resp.raise_for_status()
        return slug

    async def check_updates(self, last_update: datetime, id_data: Dict[str, Sequence[MangaEntry]]) -> List[UpdateEntry]:
        updates = []
        last_updated_int = int(last_update.timestamp())
        if "*" in id_data:
            async with self.bot.session.get(f'{self.base_endpoint}/get_all_series') as resp:
                resp.raise_for_status()
                data: AllSeries = await resp.json()
            star_data = id_data.pop("*")
            for item in data.values():
                if item['last_updated'] > last_updated_int:
                    id_data[item['slug']] = star_data
        for slug in id_data.keys():
            async with self.bot.session.get(f'{self.base_endpoint}/series/{slug}') as resp:
                resp.raise_for_status()
                data: Series = await resp.json()
            for chapter_num, chapter in data['chapters'].items():
                group_pages, group_release_date, group_id = get_preferred_chapter_data(chapter, data['preferred_sort'])
                print(group_release_date, last_updated_int, group_release_date >= last_updated_int)
                if group_release_date >= last_updated_int:
                    embed = Embed(title=f"New chapter released! {data['title']} Chapter {chapter_num}",
                                  url=f"{self.base_endpoint}/read/manga/{slug}/{chapter_num}",
                                  timestamp=datetime.fromtimestamp(group_release_date))
                    embed.set_image(
                        url=f"{self.website_endpoint}/media/manga/{slug}/chapters/{chapter['folder']}/{group_id}/"
                            f"{group_pages[0]}")
                    if chapter['title']:
                        embed.title += f": {chapter['title']}"
                    for item in id_data[slug]:
                        updates.append(UpdateEntry(item, f"{data['title']} Chapter {chapter_num}", embed=embed))
        return updates
