from discord import ButtonStyle
from discord.ui import Button, View


class PauseOrUnpause(View):
    def __init__(self, id: int):
        super().__init__(timeout=1)
        self.add_item(Button(style=ButtonStyle.primary, label="Pause", custom_id="pause_id_" + str(id)))
        self.add_item(Button(style=ButtonStyle.danger, label="Unsubscribe", custom_id="unpause_id_" + str(id)))
