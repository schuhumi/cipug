from typing import Any, TypeVar

JsonBaseType = str | float | int | bool | None
JsonType = dict[str, "JsonType"] | list["JsonType"] | JsonBaseType
JsonDictType = dict[str, "JsonType"]

T = TypeVar("T")

def ensure_type(o: Any, t: type[T], msg: str = "") -> T:
    if not isinstance(o, t):
        raise TypeError(f"Expected {t.__name__}, got {type(o).__name__}. {msg}")
    return o
