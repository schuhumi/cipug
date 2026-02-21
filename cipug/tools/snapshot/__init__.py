from cipug.tools import Toolbox

from .base import SnapshotCheckTool, SnapshotCreationTool
from .btrbk import Btrbk
from .snapper import Snapper
from .zfs import Zfs

snapshot_creation_tools = Toolbox[type[SnapshotCreationTool]]([
    Snapper,
    Zfs,
])

snapshot_check_tools = Toolbox[type[SnapshotCheckTool]]([
    Btrbk,
    Snapper,
    Zfs,
])

__all__ = [
    "Btrbk",
    "Snapper",
    "SnapshotCheckTool",
    "SnapshotCreationTool",
    "snapshot_check_tools",
    "snapshot_creation_tools",
]
