from tests.mock_tools.tools.base import Action, MockTool


class Systemctl(MockTool):
    name: str = "systemctl"

    def run(self, argv: list[str]) -> Action:
        match argv[1:]:
            case ["--user", "restart", _] | ["restart", _]:
                return Action()
        return Action(
            returncode=99, stderr="Error: Invalid command for systemd MockTool"
        )
