from typing import Any, MutableMapping

from .messages import message_mapping


class BaseError(Exception):
    pass


class Error(BaseError):
    """A class for raising errors to the main handler."""

    def __init__(self, code: int, mapping: MutableMapping[str, Any] = None, **kwargs: Any):
        if kwargs is None:
            kwargs = {}
        mapping.update(kwargs)
        super().__init__(f"[MRBErrno {code}] " + message_mapping[code].format_map(kwargs))
        self.code = code


class ErrorWithContext(BaseError):
    def __init__(self, code: int, extra: str, mapping: MutableMapping[str, Any] = None, **kwargs: Any):
        if kwargs is None:
            kwargs = {}
        mapping.update(kwargs)
        super().__init__(f"[MRBErrno {code}] " + (message_mapping[code] + f" ({extra})").format_map(kwargs))
        self.code = code
        self.extra = extra
