
from . import exit_code
from .config import Config
from .log import log
from .resolver import Image_Version_Resolver
from .service import Service
from .tools.container import ComposeTool, ContainerTool, QuadletTool
from .tools.snapshot import SnapshotCreationTool
from .tools.version_modifier import Env, Quadlet, VersionModifierTool
from .typing import Success
from .utils import get_services


class Updater:
    def __init__(self, resolver: Image_Version_Resolver, snapshot_creation_tool: SnapshotCreationTool | None):
        self.config = Config()
        self.resolver = resolver
        self.snapshot_creation_tool = snapshot_creation_tool
        self.vmt_cls: type[VersionModifierTool]
        self.container_tool_cls: type[ContainerTool]
        if "compose" in self.config["COMPOSE_TOOL"]:
            self.vmt_cls = Env
            self.container_tool_cls = ComposeTool
        elif self.config["COMPOSE_TOOL"] == "quadlet":
            self.vmt_cls = Quadlet
            self.container_tool_cls = QuadletTool
        else:
            raise ValueError(f'Unknown CIPUG_COMPOSE_TOOL {self.config["COMPOSE_TOOL"]}')
        self.vmt_cls.assert_dependencies()
        self.services: list[Service] = get_services(self.vmt_cls)
        self.container_tool_cls.assert_dependencies()
        self.container_tool = self.container_tool_cls()

    def _cater_for_snapshot(self, service: Service, vmt: VersionModifierTool) -> Success:
        if self.snapshot_creation_tool is not None:
            log(f"Taking a snapshot of {service.path} using {self.snapshot_creation_tool.name}..")
            try:
                self.snapshot_creation_tool.create_snapshot(service, vmt)
            except Exception as e:
                log.error(f'Cannot update service "{service.name}", because snapshotting failed: {e}')
                return False
        return True

    def _cater_for_updating_cnt_pin(self, service: Service, vmt: VersionModifierTool) -> Success:
        log("Writing updated hashes for container pinning..")
        try:
            vmt.write_hashes()
        except Exception as e:
            log.error(f'Cannot update service "{service.name}", because writing hashes file failed: {e}')
            return False
        return True

    def _cater_for_image_pull(self, service: Service) -> Success:
        if self.config["SERVICE_PULL"]:
            log(f'Pulling images for service "{service.name}"..')
            return self.container_tool.pull(service)
        return True

    def _cater_for_restart(self, service: Service) -> Success:
        if self.config["SERVICE_STOP_START"]:
            log(f'Restarting service "{service.name}"..')
            return self.container_tool.restart(service)
        return True

    def update_service(self, service: Service) -> exit_code.Exit_Code | None:
        log(f'Working on service "{service.name}"', highlight=True)

        vmt: VersionModifierTool = self.vmt_cls(service, self.resolver)  # Version Modifier Tool

        if vmt.has_updates(logging=True):
            log(f'Changes pending for "{service.name}"')
        else:
            log(f'No changes for "{service.name}", done.')
            return

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
