from cipug.tools import Toolbox

from .base import ContainerTool
from .compose import ComposeTool
from .quadlet import QuadletTool

container_tools = Toolbox[type[ContainerTool]]([
    ComposeTool,
    QuadletTool
])

__all__ = [
    "ComposeTool",
    "ContainerTool",
    "QuadletTool",
    "container_tools",
]
