import re

from .base import Guya

class MahouShoujoBu(Guya):
    source_name = 'MahouShoujoBu'
    url_regex = re.compile(r'^https://mahoushoujobu.com/read/manga/([\w-]+)', re.IGNORECASE)

    base_endpoint = 'https://mahoushoujobu.com/api'
    website_endpoint = 'https://mahoushoujobu.com'
