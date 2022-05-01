from discord import ButtonStyle
from discord.ui import Button, View


class ThreadActions(View):
    def __init__(self, id: int):
        super().__init__(timeout=1)
        self.add_item(
            Button(
                style=ButtonStyle.primary,
                label="Subscribe",
                custom_id="subscribe_id_" + str(id),
                row=0,
            )
        )
        self.add_item(
            Button(
                style=ButtonStyle.danger,
                label="Unsubscribe",
                custom_id="unsubscribe_id_" + str(id),
                row=0,
            )
        )
        self.add_item(
            Button(
                style=ButtonStyle.primary,
                label="Pause",
                custom_id="pause_id_" + str(id),
                row=1,
            )
        )
        self.add_item(
            Button(
                style=ButtonStyle.success,
                label="Unpause",
                custom_id="unpause_id_" + str(id),
                row=1,
            )
        )
        self.add_item(
            Button(
                style=ButtonStyle.primary,
                label="Customize",
                custom_id="customize_id_" + str(id),
                row=1,
            )
        )
