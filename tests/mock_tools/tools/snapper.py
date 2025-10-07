from tests.mock_tools.tools.base import MockTool, Action
import json


class Snapper(MockTool):
    name: str = "snapper"
    _configs: list[dict[str, str]] = [
        {
            "config": "testconf-1",
            "subvolume": "/fake/btrfs/subvolume/1",
        },
        {
            "config": "testconf-2",
            "subvolume": "/fake/btrfs/subvolume/2",
        },
    ]

    @property
    def _config_names(self) -> list[str]:
        return [entry["config"] for entry in self._configs]

    def run(self, argv: list[str]) -> Action:
        match argv[1:]:  # argv[0] is /path/to/snapper
            case ["--jsonout", "list-configs"]:
                # Print the mockup configs
                stdout = json.dumps(
                    {"configs": self._configs},
                    indent=2,
                )
                return Action(stdout=stdout)
            case ["-c", config_name, "create", "--description", message]:
                if config_name in self._config_names:
                    # pretend we successfully took a snapshot
                    return Action()
                else:
                    return Action(stderr="Unknown config.", returncode=1)

        return Action(
            returncode=99, stderr="Error: Invalid command for Snapper MockTool"
        )
