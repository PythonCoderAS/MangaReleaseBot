from discord import ButtonStyle
from discord.ui import Button, View


class SubscribeOrUnsubscribe(View):
    def __init__(self, id: int):
        super().__init__(timeout=1)
        self.add_item(Button(style=ButtonStyle.primary, label="Subscribe", custom_id="subscribe_id_" + str(id)))
        self.add_item(Button(style=ButtonStyle.danger, label="Unsubscribe", custom_id="unsubscribe_id_" + str(id)))
