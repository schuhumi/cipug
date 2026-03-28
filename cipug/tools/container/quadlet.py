
import subprocess

from cipug import exit_code
from cipug.config import Config
from cipug.log import log
from cipug.service import Service
from cipug.tools.version_modifier.quadlet import ContainerFile
from cipug.typing import Success

from .base import ContainerTool


class QuadletTool(ContainerTool):
    @classmethod
    def assert_dependencies(cls):
        config = Config()
        cp = subprocess.run(
            [*config["CONTAINER_TOOL"].split(" "), "ps"],
            check=False,
            capture_output=True
        )
        ret = cp.returncode
        if ret != 0:
            print(cp.stdout.decode(), cp.stderr.decode())
            log.error(
                f'Failed to use {config["CONTAINER_TOOL"]}',
                exit_code=exit_code.TOOL_ERROR
            )

        cp = subprocess.run(
            [*config["CONTAINER_TOOL"].split(" "), "quadlet", "list"],
            check=False,
            capture_output=True
        )
        ret = cp.returncode
        if ret != 0:
            print(cp.stdout.decode(), cp.stderr.decode())
            log.error(
                f'Failed to use {config["COMPOSE_TOOL"]}',
                exit_code=exit_code.TOOL_ERROR
            )

    def __init__(self) -> None:
        self.config = Config()

    def get_units(self, svc: Service) -> list[str]:
        units: list[str] = []
        for each in svc.path.glob("*.container"):
            cf = ContainerFile(each)
            units.append(cf.container_name)
        return units

    def _cmd(self, svc: Service, cmd: str) -> Success:
        ret = subprocess.run(
            ["systemctl", "--user", cmd, *self.get_units(svc)], check=False
        ).returncode
        if ret != 0:
            log.error(f'Failed to {cmd} service "{svc.name}" (returncode {ret})')
            return False
        return True

    def install(self, svc: Service) -> Success:
        cp = subprocess.run(
            [
                *self.config["CONTAINER_TOOL"].split(" "),
                "quadlet",
                "install",
                "-r",
                *svc.path.glob("*.container"),
                *svc.path.glob("*.network"),
            ],
            check=False
        )
        ret = cp.returncode
        if ret != 0:
            log.error(f'Failed to quadlet install {svc} (returncode {ret})')
            return False
        cp = subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            check=False
        )
        ret = cp.returncode
        if ret != 0:
            log.error(f'Failed to reload systemd user units (returncode {ret})')
            return False
        return True

    def start(self, svc: Service) -> Success:
        return self.install(svc) and self._cmd(svc, "start")

    def stop(self, svc: Service) -> Success:
        return self._cmd(svc, "stop")

    def restart(self, svc: Service) -> Success:
        return self.install(svc) and self._cmd(svc, "restart")

    def pull(self, svc: Service) -> Success:
        for each in svc.path.glob("*.container"):
            cf = ContainerFile(each)
            image_hashed = cf.image_hashed
            if image_hashed is None:
                continue
            cp = subprocess.run(
                [*self.config["CONTAINER_TOOL"].split(" "), "pull", image_hashed],
                check=False
            )
            ret = cp.returncode
            if ret != 0:
                log.error(f'Failed to pull image {image_hashed} (returncode {ret})')
                return False
        return True
