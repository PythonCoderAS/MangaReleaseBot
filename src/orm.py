from tortoise import Tortoise

from .models import MangaEntry, Metadata, Ping, ThreadData  # noqa

TORTOISE_ORM = {
    "connections": {
        "default": {
            'engine': 'tortoise.backends.asyncpg',
            "credentials": {
                "user": "mangareleasebot",
                "password": "mangareleasebot",
                "database": "mangareleasebot",
                "host": "localhost",
                "port": 5432
            }
        },
    },
    "apps": {
        "models": {
            "models": [__name__, "aerich.models"],
            "default_connection": "default",
        },
    },
    "use_tz": True,
    "maxsize": 20,
}


async def init():
    """Initialize the ORM."""
    # Here we connect to a SQLite DB file.
    # also specify the app name of "models"
    # which contain models from "app.models"
    await Tortoise.init(TORTOISE_ORM)
