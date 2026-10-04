import re
import subprocess
from datetime import datetime

from . import exit_code
from .colors import colors
from .config import Config
from .env import Env
from .log import log
from .resolver import Image_Version_Resolver
from .service import Service
from .tools.snapshot import SnapshotCreationTool
from .utils import get_services


class Updater:
    def __init__(self, resolver: Image_Version_Resolver, snapshot_creation_tool: SnapshotCreationTool | None):
        self.config = Config()
        self.resolver = resolver
        self.snapshot_creation_tool = snapshot_creation_tool
        self.services: list[Service] = get_services()

    def _update_image_hashes(self, env: Env):
        for key in list(env.keys()):  # Dict size will change, hence copy env.keys into a list
            if key.startswith("SERVICE_") and key.endswith("_IMAGE_TAGGED"):
                entry_name = key.removeprefix("SERVICE_").removesuffix("_IMAGE_TAGGED")
                image_tagged = env[key]

                # Check for environment variables in the tagged image (${VAR} format)
                def replace_env_vars(s: str, vars: dict[str, str]):
                    def replace_var(match: re.Match[str]) -> str:
                        var_name: str = match.group(1)
                        fallback: str = match.group(0)
                        return vars.get(var_name, fallback)

                    pattern = r"\${([A-Za-z0-9_]+)}"
                    return re.sub(pattern, replace_var, s)

                # Apply environment variable substitution
                interpolated_image = replace_env_vars(image_tagged, env)
                if interpolated_image != image_tagged:
                    log.verbose(f"Interpolated image name: {image_tagged} → {interpolated_image}")
                    image_tagged = interpolated_image

                log.verbose(f'Found tagged image entry for "{entry_name}": {image_tagged}')

                current_hash = env.get("_".join(["SERVICE", entry_name, "IMAGE", "HASHED"]), None)
                if current_hash is None:
                    log.verbose(
                        f'There\'s no hashed image reference for "{entry_name}"'
                        f" in {self.config['ENV_FILE_NAME']} currently"
                    )
                else:
                    log.verbose(f'The current hashed image reference for "{entry_name}" is: {current_hash}')

                new_hash = self.resolver.resolve_image_version(image_tagged)

                if new_hash == current_hash:
                    log(f"{entry_name}: {image_tagged} stays at {current_hash}")
                else:
                    env["_".join(["SERVICE", entry_name, "IMAGE", "HASHED"])] = new_hash
                    log(f"{colors.Green}{entry_name}: {image_tagged} is now at {new_hash}{colors.Reset}")

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

    def _cater_for_snapshot(self, service: Service) -> bool:
        if self.snapshot_creation_tool is not None:
            log(f"Taking a snapshot of {service.path} using {self.snapshot_creation_tool.name}..")
            try:
                self.snapshot_creation_tool.create_snapshot(
                    service,
                    message=f"Update container images {datetime.today()!s}"
                )
            except Exception as e:
                log.error(f'Cannot update service "{service.name}", because snapshotting failed: {e}')
                return False
        return True

    def _cater_for_updating_env_file(self, env: Env, service: Service) -> bool:
        log(f"Writing updated {env.path} configuration..")
        try:
            env.write()
        except Exception as e:
            log.error(f'Cannot update service "{service.name}", because writing .env file failed: {e}')
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

        env_file = service.path / self.config["ENV_FILE_NAME"]
        if not env_file.is_file():
            log.error(f"File {env_file} not found, cannot update service.")
            return exit_code.FILE_NOT_FOUND
        env = Env(env_file)

        log.vverbose(
            f"Searching {self.config['ENV_FILE_NAME']} for SERVICE_*_IMAGE_TAGGED "
            "entries that should get resolved to SERVICE_*_IMAGE_HASHED entries."
        )

        self._update_image_hashes(env)

        if env.has_changes():
            log(f'Changes pending for "{service.name}"')
        else:
            log(f'No changes for "{service.name}", done.')
            return

        if not self._check_permission_compose_tool(service):
            return exit_code.TOOL_ERROR

        if not self._cater_for_snapshot(service):
            return exit_code.SNAPSHOT_ERROR

        if not self._cater_for_updating_env_file(env, service):
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
