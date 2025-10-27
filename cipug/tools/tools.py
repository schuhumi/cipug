from abc import ABC
from typing import Generic, TypeVar


class Tool(ABC):
    name: str


T = TypeVar('T', bound=type[Tool])

class Toolbox(Generic[T]):
    """Collection of tools that serve the same purpose."""
    tools: list[T]

    def __init__(self, tools: list[T]):
        self.tools = tools

    def get_by_name(self, name: str) -> T:
        for tool in self.tools:
            if tool.name == name:
                return tool
        raise KeyError(f"Tool '{name}' not found")

    def get_names(self) -> list[str]:
        return [tool.name for tool in self.tools]
