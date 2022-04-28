from typing import TypeVar

T = TypeVar("T")


def batch(items: list[T], batch_limit: int = 100) -> list[list[T]]:
    """
    Batch items into batches of batch_limit size.
    """
    return [items[i : i + batch_limit] for i in range(0, len(items), batch_limit)]
