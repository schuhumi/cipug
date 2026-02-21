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
                
                # timestamps in seconds
                t1 = 1708527600 # 2024-02-21 15:00:00
                t2 = 1708531200 # 2024-02-21 16:00:00
                
                return Action(stdout=(
                    f"{dataset}@cipug-2024-02-21-1500\t{t1}\n"
                    f"{dataset}@cipug-2024-02-21-1600\t{t2}\n"
                    f"{dataset}@other-snapshot\t{t2}\n"
                ))

            case ["snapshot", snapshot_name]:
                # Mock creating snapshot
                if "@" in snapshot_name:
                    return Action()
                else:
                    return Action(stderr="invalid snapshot name\n", returncode=1)

        return Action(
            returncode=99, stderr=f"Error: Invalid command for Zfs MockTool: {argv}"
        )
