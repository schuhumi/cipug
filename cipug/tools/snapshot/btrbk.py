from datetime import datetime

from cipug.log import log
from cipug.service import Service

from .base import SnapshotCheckTool


class Btrbk(SnapshotCheckTool):
    name = "btrbk"
    default_max_age = 36.0  # in hours

    def __init__(self):
        from cipug.config import Config  # Import here to prevent circular import

        self.config = Config()

    @classmethod
    def assert_dependencies(cls):
        """We do not need to call btrbk. It doesn't even need to be installed, as backups
        can be initiated by the backup server. Therefore we do not have any dependencies
        to verify.
        """
        return

    def get_last_snapshot_date(self, service: Service) -> datetime | None:
        subdir = self.config["SNAPSHOTS_DIR_BTRBK"]
        if not subdir:
            return None
        dir = service.path / subdir
        if not dir.is_dir():
            log.error(f"{dir} is not a folder")

        try:
            latest = sorted(dir.glob("*.*T*"), reverse=True)[0]
        except IndexError:
            # Empty list -> no snapshots
            return None

        datestr: str = latest.name.split(".", -1)[1]
        # For example: 20250626T0100
        return datetime.strptime(datestr, "%Y%m%dT%H%M")
