import subprocess

from . import exit_code
from .config import Config
from .log import log
from .resolver import Image_Version_Resolver
from .service import Service
from .tools.snapshot import SnapshotCreationTool
from .tools.version_modifier import Env, VersionModifierTool
from .utils import get_services


class Updater:
    def __init__(self, resolver: Image_Version_Resolver, snapshot_creation_tool: SnapshotCreationTool | None):
        self.config = Config()
        self.resolver = resolver
        self.snapshot_creation_tool = snapshot_creation_tool
        self.services: list[Service] = get_services()

    def _check_permission_compose_tool(self, service: Service) -> bool:
        log(f'Ensuring permission for "{self.config["COMPOSE_TOOL"]}"..')
        cp = subprocess.run(
            [*self.config["COMPOSE_TOOL"].split(" "), "ps"], check=False, cwd=service.path, capture_output=True
        )
        ret = cp.returncode
        if ret != 0:
            print(cp.stdout.decode(), cp.stderr.decode())
            log.error(
                f'Cannot update service "{service.name}", because '
                f'cannot use "{self.config["COMPOSE_TOOL"]}" (returncode {ret})'
            )
            return False
        return True

    def _cater_for_snapshot(self, service: Service, vmt: VersionModifierTool) -> bool:
        if self.snapshot_creation_tool is not None:
            log(f"Taking a snapshot of {service.path} using {self.snapshot_creation_tool.name}..")
            try:
                self.snapshot_creation_tool.create_snapshot(service, vmt)
            except Exception as e:
                log.error(f'Cannot update service "{service.name}", because snapshotting failed: {e}')
                return False
        return True

    def _cater_for_updating_cnt_pin(self, service: Service, vmt: VersionModifierTool) -> bool:
        log("Writing updated hashes for container pinning..")
        try:
            vmt.write_hashes()
        except Exception as e:
            log.error(f'Cannot update service "{service.name}", because writing hashes file failed: {e}')
            return False
        return True

    def _cater_for_image_pull(self, service: Service) -> bool:
        if self.config["SERVICE_PULL"]:
            log(f'pulling images for service "{service.name}"..')
            ret = subprocess.run(
                [*self.config["COMPOSE_TOOL"].split(" "), "pull"], check=False, cwd=service.path
            ).returncode
            if ret != 0:
                log.error(f'Cannot update service "{service.name}", because pulling images failed (returncode {ret})')
                return False
        return True

    def _cater_for_restart(self, service: Service) -> bool:
        if self.config["SERVICE_STOP_START"]:
            if self.config["STOP_START_METHOD"] == "compose":
                log(f'stopping service "{service.name}"..')
                ret = subprocess.run(
                    [*self.config["COMPOSE_TOOL"].split(" "), "down"], check=False, cwd=service.path
                ).returncode
                if ret != 0:
                    log.error(f'Failed to stop service "{service.name}" (returncode {ret})')
                    return False

                log(f'Starting "{service.name}" service..')
                ret = subprocess.run(
                    [*self.config["COMPOSE_TOOL"].split(" "), "up", "-d"], check=False, cwd=service.path
                ).returncode
                if ret != 0:
                    log.error(f'Failed to start service "{service.name}" (returncode {ret})')
                    return False
            elif self.config["STOP_START_METHOD"] in ["systemd-system", "systemd-user"]:
                systemd_service = f"{self.config['COMPOSE_TOOL'].replace(' ', '-')}@{service.name}"
                log(f"Restarting {self.config['STOP_START_METHOD'].replace('-', ' ')} service {systemd_service}")
                cmdlist = ["systemctl"]
                if "-user" in self.config["STOP_START_METHOD"]:
                    cmdlist.append("--user")
                cmdlist += ["restart", systemd_service]
                ret = subprocess.run(cmdlist, check=False, cwd=service.path).returncode
                if ret != 0:
                    log.error(f'Failed to restart service "{service.name}" (returncode {ret})')
                    return False
            else:
                log.error(
                    f"Failed to restart service \"{service.name}\". Unknown method '{self.config['STOP_START_METHOD']}'"
                )
                return False
        return True

    def update_service(self, service: Service) -> exit_code.Exit_Code | None:
        log(f'Working on service "{service.name}"', highlight=True)

        vmt: VersionModifierTool = Env(service, self.resolver)  # Version Modifier Tool

        if vmt.has_updates(logging=True):
            log(f'Changes pending for "{service.name}"')
        else:
            log(f'No changes for "{service.name}", done.')
            return

        if not self._check_permission_compose_tool(service):
            return exit_code.TOOL_ERROR

        if not self._cater_for_snapshot(service, vmt):
            return exit_code.SNAPSHOT_ERROR

        if not self._cater_for_updating_cnt_pin(service, vmt):
            return exit_code.ENV_ERROR

        if not self._cater_for_image_pull(service):
            return exit_code.IMAGE_PULL_ERROR

        if not self._cater_for_restart(service):
            return exit_code.SERVICE_RESTART_ERROR

    def update_all_services(self) -> list[exit_code.Exit_Code]:
        errors: list[exit_code.Exit_Code] = []
        for service in self.services:
            e = self.update_service(service)
            if e is not None:
                errors.append(e)
        return errors
