from os import getenv

if getenv("DEBUG", "0") == "1":
    import logging

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
        )
    )
    logger.addHandler(handler)
    discord = logging.getLogger("discord")
    discord.setLevel(logging.WARNING)  # We want discord warns
    discord.addHandler(handler)
