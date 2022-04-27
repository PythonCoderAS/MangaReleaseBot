from typing import Any, Callable, Coroutine, Optional

from discord import ButtonStyle, Interaction
from discord.ui import Button, View, button


class Confirm(View):
    def __init__(
        self,
        confirm_callback: Callable[
            ["Confirm", Interaction, Button], Coroutine[None, None, Any]
        ],
        deny_callback: Optional[
            Callable[["Confirm", Interaction, Button], Coroutine[None, None, Any]]
        ] = None,
        *,
        timeout: Optional[float] = 180.0
    ):
        super().__init__(timeout=timeout)
        self.confirm_callback = confirm_callback
        self.deny_callback = deny_callback

    async def update_buttons(self, interaction: Interaction):
        self.confirm.disabled = True
        self.deny.disabled = True
        interaction.response.edit_message(view=self)

    @button(label="Confirm", style=ButtonStyle.success)
    async def confirm(self, interaction: Interaction, button_obj: Button):
        await self.update_buttons(interaction)
        await self.confirm_callback(self, interaction, button_obj)

    @button(label="Deny", style=ButtonStyle.danger)
    async def deny(self, interaction: Interaction, button_obj: Button):
        await self.update_buttons(interaction)
        if self.deny_callback:
            await self.deny_callback(self, interaction, button_obj)
