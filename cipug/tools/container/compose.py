import subprocess

from cipug import exit_code
from cipug.config import Config
from cipug.log import log
from cipug.service import Service
from cipug.typing import Success

from .base import ContainerTool


class ComposeTool(ContainerTool):
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
            [*config["COMPOSE_TOOL"].split(" "), "--version"],
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

    def _compose_cmd(self, svc: Service, cmd: list[str]) -> Success:
        ret = subprocess.run(
            [*self.config["COMPOSE_TOOL"].split(" "), *cmd], check=False, cwd=svc.path
        ).returncode
        if ret != 0:
            log.error(f'Failed to {cmd} service "{svc.name}" (returncode {ret})')
            return False
        return True

    def _systemd_cmd(self, svc: Service, cmd: list[str]) -> Success:
        systemd_service = f"{self.config['COMPOSE_TOOL'].replace(' ', '-')}@{svc.name}"
        cmdlist = ["systemctl"]
        if "-user" in self.config["STOP_START_METHOD"]:
            cmdlist.append("--user")
        cmdlist += [*cmd, systemd_service]
        ret = subprocess.run(cmdlist, check=False, cwd=svc.path).returncode
        if ret != 0:
            log.error(f'Failed to {cmd} {systemd_service} service "{svc.name}" (returncode {ret})')
            return False
        return True

    def _cmd(self, svc: Service, compose_cmd: list[str], systemd_cmd: list[str]) -> Success:
        if self.config["STOP_START_METHOD"] == "compose":
            return self._compose_cmd(svc, compose_cmd)
        elif self.config["STOP_START_METHOD"] in ["systemd-system", "systemd-user"]:
            return self._systemd_cmd(svc, systemd_cmd)
        else:
            log.error(f"Unknown method '{self.config['STOP_START_METHOD']}'")
            return False

    def start(self, svc: Service) -> Success:
        return self._cmd(svc, ["up", "-d"], ["start"])

    def stop(self, svc: Service) -> Success:
        return self._cmd(svc, ["down"], ["stop"])

    def restart(self, svc: Service) -> Success:
        if self.config["STOP_START_METHOD"] == "compose":
            return self.stop(svc) and self.start(svc)
        elif self.config["STOP_START_METHOD"] in ["systemd-system", "systemd-user"]:
            return self._systemd_cmd(svc, ["restart"])
        else:
            log.error(f"Unknown method '{self.config['STOP_START_METHOD']}'")
            return False

    def pull(self, svc: Service) -> Success:
        return self._compose_cmd(svc, ["pull"])
