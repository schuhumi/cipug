import os
import json
from tests.mock_tools.tools.base import MockTool, Action


class Snapper(MockTool):
    name: str = "snapper"
    configs: list[dict[str, str]] = [
        {
            "config": "testconf-1",
            "subvolume": "/fake/btrfs/subvolume/1",
        },
        {
            "config": "testconf-2",
            "subvolume": "/fake/btrfs/subvolume/2",
        },
    ]

    def __init__(self):
        super().__init__()
        # Enable adding another mock config subvolume via environment variable
        subvol: str | None = os.environ.get("MOCK_TOOL_SNAPPER_ENV_CONF", None)
        if subvol is not None:
            self.configs.append({
                "config": "envconf",
                "subvolume": subvol
            })

    @property
    def config_names(self) -> list[str]:
        return [entry["config"] for entry in self.configs]

    def run(self, argv: list[str]) -> Action:
        match argv[1:]:  # argv[0] is /path/to/snapper
            case ["--version"]:
                return Action(
                    stdout=(
                        "snapper 0.11.0\n"
                        "libsnapper 7.4.3\n"
                        "flags btrfs,bcachefs,lvm,no-ext4,xattrs,rollback,btrfs-quota,selinux\n"
                    )
                )
            case ["--jsonout", "list-configs"]:
                # Print the mockup configs
                stdout = json.dumps(
                    {"configs": self.configs},
                    indent=2,
                )
                return Action(stdout=stdout)
            case ["-c", config_name, "create", "--description", message]:
                if config_name in self.config_names:
                    # pretend we successfully took a snapshot
                    return Action()
                else:
                    return Action(stderr="Unknown config.", returncode=1)

        return Action(
            returncode=99, stderr="Error: Invalid command for Snapper MockTool"
        )
