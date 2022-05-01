from functools import wraps
from typing import Any, Callable, Optional, TYPE_CHECKING, TypeVar

from discord import InteractionResponse, Webhook
from discord.abc import Messageable

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot

_T = TypeVar("_T")

original_send = Messageable.send
interaction_response_message = InteractionResponse.send_message
interaction_response_modal = InteractionResponse.send_modal
webhook_send = Webhook.send

bot: Optional["MangaReleaseBot"] = None  # Fill this in!


def patch(key: str):
    def patched(function: Callable[..., _T]):
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> _T:
            if bot is None:
                pass
            else:
                setattr(
                    bot.config_manager, key, getattr(bot.config_manager, key, 0) + 1
                )
            return function(*args, **kwargs)

        return wrapper

    return patched


Messageable.send = patch("messages")(original_send)
InteractionResponse.send_message = patch("messages")(interaction_response_message)
InteractionResponse.send_modal = patch("modals")(interaction_response_modal)
Webhook.send = patch("messages")(webhook_send)
