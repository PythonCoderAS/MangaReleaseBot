from typing import Any, Iterator, MutableMapping, TypeVar

T = TypeVar("T")


def batch(items: list[T], batch_limit: int = 100) -> list[list[T]]:
    """
    Batch items into batches of batch_limit size.
    """
    return [items[i : i + batch_limit] for i in range(0, len(items), batch_limit)]


class AttributeDictionary(MutableMapping[str, Any]):
    """Access an object's attributes using keys."""

    @property
    def actual_attr_keys(self) -> list[str]:
        has_dict = hasattr(self.obj, "__dict__")
        keys = self.obj.__slots__ if hasattr(self.obj, "__slots__") else dir(self.obj)
        if has_dict:
            keys.extend(self.obj.__dict__.keys())
        return keys

    def __init__(self, obj: Any):
        self.obj = obj

    def __setitem__(self, __k: str, __v: Any):
        setattr(self.obj, __k, __v)

    def __delitem__(self, __v: str):
        delattr(self.obj, __v)

    def __getitem__(self, __k: str) -> Any:
        return getattr(self.obj, __k)

    def __len__(self) -> int:
        return len(self.actual_attr_keys)

    def __iter__(self) -> Iterator[str]:
        yield from self.actual_attr_keys
