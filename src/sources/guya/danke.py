import re

from .base import Guya

class Danke(Guya):
    source_name = 'danke.moe'
    url_regex = re.compile(r'^https://danke.moe/read/manga/([\w-]+)', re.IGNORECASE)

    base_endpoint = 'https://danke.moe/api'
    website_endpoint = 'https://danke.moe'
