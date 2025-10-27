from abc import ABC, abstractmethod
from datetime import datetime

from cipug.service import Service
from cipug.tools import Tool


class SnapshotCreationTool(Tool, ABC):
    @abstractmethod
    def create_snapshot(self, service: Service, message: str): ...


class SnapshotCheckTool(Tool, ABC):
    """Used to verify that a recent snapshot exists"""

    # Can be overridden with the SNAPSHOTS_MAX_AGE_XXX setting, where XXX is the
    # name attribute of this class in upper case.
    default_max_age: float  # in hours

    @abstractmethod
    def get_last_snapshot_date(self, service: Service) -> datetime | None: ...
