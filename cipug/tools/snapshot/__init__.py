from cipug.tools import Toolbox

from .base import SnapshotCheckTool, SnapshotCreationTool
from .btrbk import Btrbk
from .snapper import Snapper

snapshot_creation_tools = Toolbox[type[SnapshotCreationTool]]([
    Snapper,
])

snapshot_check_tools = Toolbox[type[SnapshotCheckTool]]([
    Btrbk,
    Snapper,
])

__all__ = [
    "Btrbk",
    "Snapper",
    "SnapshotCheckTool",
    "SnapshotCreationTool",
    "snapshot_check_tools",
    "snapshot_creation_tools",
]
