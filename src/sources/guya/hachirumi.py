import re

from .base import Guya


class Hachirumi(Guya):
    source_name = "Hachirumi"
    url_regex = re.compile(
        r"^https://hachirumi.com/read/manga/([\w-]+|\*)", re.IGNORECASE
    )

    base_endpoint = "https://hachirumi.com/api"
    website_endpoint = "https://hachirumi.com"
