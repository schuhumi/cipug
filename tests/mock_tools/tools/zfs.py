import os
from pathlib import Path

from tests.mock_tools.tools.base import Action, MockTool


class Zfs(MockTool):
    name: str = "zfs"

    def run(self, argv: list[str]) -> Action:
        match argv[1:]:  # argv[0] is /path/to/zfs
            case ["--version"]:
                return Action(
                    stdout=(
                        "zfs-2.1.5-1ubuntu6~22.04.1\n"
                        "zfs-kmod-2.1.5-1ubuntu6~22.04.1\n"
                    )
                )
            case ["list", "-H", "-o", "name", path]:
                # Mock finding dataset for path
                # Allow any path, just derive a dataset name
                if "error_service" in path:
                     return Action(stderr=f"cannot open '{path}': dataset does not exist\n", returncode=1)

                # Derive dataset name from path for valid cases
                # e.g. /tmp/xyz/services/fake_service -> tank/services/fake_service
                service_name = Path(path).name
                return Action(stdout=f"tank/services/{service_name}\n")
            case ["list", "-t", "snapshot", "-H", "-o", "name,creation", "-p", "-d", "1", dataset]:
                # Mock listing snapshots
                if "error_service" in dataset:
                     return Action(stderr=f"cannot open '{dataset}': dataset does not exist\n", returncode=1)

                service_name = dataset.split("/")[-1]

                # Check if a snapshot was created during this test by looking for our mock file
                conf_dir = os.environ.get("MOCK_TOOL_ZFS_ENV_CONF")
                if conf_dir and Path(conf_dir).name == service_name:
                    mock_file = Path(conf_dir) / ".mock_has_snapshots"
                    if not mock_file.exists():
                        return Action(stdout="")

                import time
                now = int(time.time())
                t1 = now - 3600
                t2 = now - 1800

                return Action(stdout=(
                    f"{dataset}@cipug-mock-1\t{t1}\n"
                    f"{dataset}@cipug-mock-2\t{t2}\n"
                    f"{dataset}@other-snapshot\t{t2}\n"
                ))

            case ["snapshot", snapshot_name]:
                # Mock creating snapshot
                if "@" in snapshot_name:
                    conf_dir = os.environ.get("MOCK_TOOL_ZFS_ENV_CONF")
                    if conf_dir:
                        (Path(conf_dir) / ".mock_has_snapshots").touch()
                    return Action()
                else:
                    return Action(stderr="invalid snapshot name\n", returncode=1)

        return Action(
            returncode=99, stderr=f"Error: Invalid command for Zfs MockTool: {argv}"
        )
