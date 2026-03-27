from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING

from cipug.service import Service
from cipug.tools import Tool

if TYPE_CHECKING:
    from cipug.tools.version_modifier import VersionModifierTool


class SnapshotCreationTool(Tool, ABC):
    @abstractmethod
    def create_snapshot(self, service: Service, vmt: "VersionModifierTool | None"): ...


class SnapshotCheckTool(Tool, ABC):
    """Used to verify that a recent snapshot exists"""

    # Can be overridden with the SNAPSHOTS_MAX_AGE_XXX setting, where XXX is the
    # name attribute of this class in upper case.
    default_max_age: float  # in hours
    uses_directory: bool = True

    @abstractmethod
    def get_last_snapshot_date(self, service: Service) -> datetime | None: ...
