from abc import ABC, abstractmethod
from typing import Generic, TypeVar


class Tool(ABC):
    name: str

    @classmethod
    @abstractmethod
    def assert_dependencies(cls):
        """Check if all dependencies the tool needs (cli programs etc..) are satisfied.
        If that's not the case, log an error with exit_code.DEPENDENCY_ERROR like this:

        log.error(
            "Dependency XYZ not found",
            exit_code=exit_code.DEPENDENCY_ERROR
        )

        This method is a class method, since the dependencies need to be checked before
        instantiating the tool, which might rely on the dependency already
        """
        ...


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
