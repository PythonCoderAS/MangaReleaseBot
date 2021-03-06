from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Pattern, Sequence, TYPE_CHECKING

from discord import Embed, File
from discord.ui import Modal

from .._patched.types.discord import Context, Interaction
from ..models import MangaEntry
from ..utils.manga import save_config

if TYPE_CHECKING:
    from ..bot import MangaReleaseBot


@dataclass(frozen=True)
class UpdateEntry:
    entry: MangaEntry
    thread_title: str
    embed: Optional[Embed] = None
    message: Optional[str] = None


class BaseModal(ABC, Modal, title="Apply Customizations"):
    def __init__(
        self,
        entry: MangaEntry,
        source: "BaseSource",
        *,
        timeout: Optional[float] = None,
    ):
        super().__init__(timeout=timeout)
        self.entry = entry
        self.source = source

    async def get_customization(
        self, interaction: Interaction
    ) -> Optional[Dict[str, Any]]:
        """Get a customization dictionary for storage.

        :param interaction: The interaction object created when the modal is submitted.
        :type interaction: Interaction
        :return: Either a dictionary of customization values or None to skip modification.
            In order to store **no** customizations, return an empty dictionary.
        :rtype: Optional[Dict[str, Any]]
        """
        raise NotImplementedError

    async def on_submit(self, interaction: Interaction):
        """Method called when the modal is submitted. Override this method to change the default behavior.

        Default behavior:

        1. First, get the dictionary of customization values from :meth:`~.get_customization`.
        2. If the value is None, send a message and return.
        3. If the value is an empty dictionary (``{}``), send a message, apply
            :attr:`~.default_customizations` from the provided :attr:`~.source` and save
            it to the database.
        4. If the value is a non-empty dictionary, send a message and save the provided
            dictionary to the database.

        :param interaction: The interaction object created when the modal is submitted.
        :type interaction: Interaction
        """
        await interaction.response.defer()
        customizations = await self.get_customization(interaction)
        await self.source.validate(self.entry, customizations)
        if customizations is None:
            await interaction.followup.send(
                f"No customizations were applied to entry #{self.entry.id}."
            )
        elif customizations == {}:
            await interaction.followup.send(
                f"Customizations for entry #{self.entry.id} were reset to default."
            )
            self.entry.extra_config = self.source.default_customizations
            await self.entry.save()
        else:
            await save_config(self.entry, customizations, interaction)


class BaseSource(ABC):
    """
    Base class for sources.
    """

    source_name: ClassVar[str]
    url_regex: ClassVar[Pattern]
    default_customizations: ClassVar[Optional[Dict[str, Any]]] = None

    def __init__(self, bot: "MangaReleaseBot"):
        self.bot = bot

    @abstractmethod
    async def get_id(self, url: str) -> Optional[str]:
        """Get the ID of the item from the URL. Return None if not found."""
        raise NotImplementedError

    async def add_item(self, ctx: Context, url: str) -> Optional[MangaEntry]:
        """Add an item to be notified of in the future."""
        item_id = await self.get_id(url)
        if item_id is None:
            await ctx.send(f"Valid manga not found for the {self.source_name} source.")
            return
        return MangaEntry(item_id=item_id, extra_config=self.default_customizations)

    async def customize(self, entry: MangaEntry) -> BaseModal:
        """Return a modal for further customization or raise :exception:`NotImplementedError`
        if there is no customization for the source.

        :param entry: The entry to customize.
        :type entry: MangaEntry
        :raises NotImplementedError: If there is no customization for the source.
        :return: The modal to be displayed.
        :rtype: BaseModal
        """
        raise NotImplementedError

    async def validate(self, entry: MangaEntry, config: Any):
        """Validate the provided configuration. Raise an :class:`.ErrorWithContext` if the configuration is invalid.

        :param entry: The entry that is getting the config
        :type entry: MangaEntry
        :param config: The configuration data
        :type config: Any
        :raises ErrorWithContext: If the configuration is invalid.
        """
        return

    @abstractmethod
    async def check_updates(
        self, last_update: datetime, data: Dict[str, Sequence[MangaEntry]]
    ) -> List[UpdateEntry]:
        """Check for updates and return a list of UpdateEntry objects."""
        raise NotImplementedError
