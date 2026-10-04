import subprocess
from datetime import datetime

from cipug import exit_code
from cipug.log import log
from cipug.service import Service

from .base import SnapshotCheckTool, SnapshotCreationTool


class Zfs(SnapshotCreationTool, SnapshotCheckTool):
    """Snapshot creation and check tool for ZFS."""

    name = "zfs"
    default_max_age = 1.5  # in hours
    uses_directory = False

    @classmethod
    def assert_dependencies(cls):
        try:
            # Check if zfs is available
            subprocess.check_call(["zfs", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.vverbose(f"Found tool: {cls.name}")
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

    def create_snapshot(self, service: Service, message: str):
        if not service.path.exists():
             raise FileNotFoundError(f"Service path {service.path} does not exist")

        # Determine dataset for path using 'zfs list'
        # zfs list -H -o name /path/to/mountpoint
        try:
            dataset_cmd = ["zfs", "list", "-H", "-o", "name", str(service.path)]
            dataset = subprocess.check_output(dataset_cmd, text=True).strip()
        except subprocess.CalledProcessError as e:
             raise Exception(f"Could not determine ZFS dataset for path {service.path}: {e}")

        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M")
        snapshot_suffix = f"cipug-{timestamp}"

        full_snapshot_name = f"{dataset}@{snapshot_suffix}"

        log(f"Creating ZFS snapshot {full_snapshot_name}...")

        cmd = ["zfs", "snapshot", full_snapshot_name]

        completed_process = subprocess.run(cmd, check=False, capture_output=True, text=True)
        if completed_process.returncode != 0:
             raise Exception(
                f"Failed to create ZFS snapshot {full_snapshot_name}, "
                f"returncode {completed_process.returncode}: {completed_process.stderr}"
            )

    def get_last_snapshot_date(self, service: Service) -> datetime | None:
        if not service.path.exists():
             return None

        # Determine dataset for path
        try:
            dataset_cmd = ["zfs", "list", "-H", "-o", "name", str(service.path)]
            dataset = subprocess.check_output(dataset_cmd, text=True).strip()
        except subprocess.CalledProcessError:
             return None

        # List snapshots for this dataset
        # -t snapshot: only snapshots
        # -H: no header
        # -o name,creation: only name and creation time
        # -p: creation time as unix timestamp (seconds)
        # -d 1: current dataset only
        try:
            snapshot_cmd = ["zfs", "list", "-t", "snapshot", "-H", "-o", "name,creation", "-p", "-d", "1", dataset]
            output = subprocess.check_output(snapshot_cmd, text=True).strip()
        except subprocess.CalledProcessError:
             return None

        if not output:
            return None

        latest_date = None
        for line in output.splitlines():
            name, creation = line.split("\t")
            if "@cipug-" in name:
                dt = datetime.fromtimestamp(int(creation))
                if latest_date is None or dt > latest_date:
                    latest_date = dt

        return latest_date
