"""Methods for managing configuration values via a database."""
from asyncio import gather
from typing import Any, Optional

from .models import Metadata


class ConfigManager:
    last_updated: int

    def __init__(self, data: dict):
        self.data = data
        self.changed = []
        self.deleted = []

    @classmethod
    async def get(cls):
        all_metadata = await Metadata.all()
        data = {}
        for item in all_metadata:
            data[item.key] = item
        return cls(data)

    def __getattr__(self, item: str) -> Optional[Any]:
        print(item)
        try:
            return self.data[item].value
        except KeyError:
            return None

    def __setattr__(self, key: str, value: Any) -> None:
        if key in ["data", "changed", "deleted"]:
            return super().__setattr__(key, value)
        if key not in self.data:
            self.data[key] = Metadata(key=key, value=value)
        else:
            self.data[key].value = value
        self.changed.append(key)

    def __delattr__(self, item: str):
        self.deleted.append(self.data[item])
        del self.data[item]

    async def save(self):
        await gather(*[self.data[item].save() for item in self.changed])
        await gather(*[item.delete() for item in self.deleted])
