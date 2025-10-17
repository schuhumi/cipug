from abc import ABC
from tests.mock_tools.tools.base import MockTool, Action

class Compose(MockTool, ABC):
    def run(self, argv: list[str]) -> Action:
        match argv[1:]:
            case ["ps"]:
                return Action()
            case ["pull"]:
                return Action()
            case ["down"]:
                return Action()
            case ["up", "-d"]:
                return Action()
        return Action(
            returncode=99, stderr=f"Error: Invalid command for {self.name} MockTool: {argv}\n"
        )

class DockerDashCompose(Compose):
    name = "docker-compose"

class PodmanDashCompose(Compose):
    name = "docker-compose"

class NoDashCompose(Compose, ABC):
    # docker and podman
    def run(self, argv: list[str]) -> Action:
        match argv[1:]:
            case ["--version"]:
                return Action(stdout=f"{self.name} version 5.6.7\n")
            case ["image", "prune", "-f"]:
                return Action()
            case ["compose", *compose_args]:
                return super().run(argv[1:])
        return Action(
            returncode=99, stderr=f"Error: Invalid command for {self.name} MockTool: {argv}\n"
        )

class DockerCompose(NoDashCompose):
    name = "docker"

class PodmanCompose(NoDashCompose):
    name = "podman"
