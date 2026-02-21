import json
import subprocess
from datetime import datetime
from pathlib import Path

from cipug import exit_code
from cipug.log import log
from cipug.service import Service

from .base import SnapshotCheckTool, SnapshotCreationTool


class Snapper(SnapshotCreationTool, SnapshotCheckTool):
    """Interact with the snapper utility. Specifically, it can create snapshots
    of subvolumes specified by volume path. It does that by going through snapper's
    configs and finding out which one belongs to that path. That way, cipug does not
    need to know the respective snapper config names from the user. It also works as a
    SnapshotCheckTool and can find the last snapshot date.
    """

    name = "snapper"
    default_max_age = 1.5  # in hours

    def __init__(self):
        from cipug.config import Config  # Import here to prevent circular import

        self.config = Config()
        self.configs = json.loads(subprocess.check_output(["snapper", "--jsonout", "list-configs"]).decode("utf-8"))[
            "configs"
        ]
        log.vverbose(f"Loaded snapper configs: \n{json.dumps(self.configs, indent=2)}")

    @classmethod
    def assert_dependencies(cls):
        try:
            out = subprocess.check_output([cls.name, "--version"], text=True).strip()
            log.vverbose(f"Found tool: {out}")
        except FileNotFoundError:
            log.error(
                f"Dependency {cls.name} not found",
                exit_code=exit_code.DEPENDENCY_ERROR
            )
        except Exception as e:
            log.error(
                f"Found dependency {cls.name}, encountered error when calling it: {e}",
                exit_code=exit_code.DEPENDENCY_ERROR
            )

    def create_snapshot(self, service: Service, message: str, image_hash: str | None = None):
        config_name = None
        for each in self.configs:
            subvol = Path(each["subvolume"])
            if subvol.resolve() == service.path.resolve():
                config_name = each["config"]
                break

        if config_name is None:
            raise KeyError(f"No snapper config found for folder {service.path}")

        completed_process = subprocess.run(
            ["snapper", "-c", config_name, "create", "--description", message], check=False
        )
        if completed_process.returncode != 0:
            raise Exception(
                f"Failed to snapshot using config {config_name}, returncode {completed_process.returncode}."
            )
            # We do not handle any stdout/stderr here, because snapper
            # wrote it there already itself when it ran

    def get_last_snapshot_date(self, service: Service) -> datetime | None:
        subdir = self.config["SNAPSHOTS_DIR_SNAPPER"]
        if not subdir:
            return None
        dir = service.path / subdir
        if not dir.is_dir():
            log.error(f"{dir} is not a folder")

        try:
            latest = sorted(dir.glob("*/info.xml"), key=lambda p: p.stat().st_ctime, reverse=True)[0]
        except IndexError:
            # Empty list -> no snapshots
            return None

        return datetime.fromtimestamp(latest.stat().st_ctime)
