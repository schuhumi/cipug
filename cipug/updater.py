from pathlib import Path
from datetime import datetime
import subprocess

from .colors import colors
from .config import Config
from .log import log
from .env import Env
from .resolver import Image_Version_Resolver
from .snapper import Snapper
from .utils import get_services
from . import exit_code

class Updater():
    def __init__(
        self,
        config: Config,
        resolver: Image_Version_Resolver,
        snapper: Snapper
    ):
        self.config = config
        self.resolver = resolver
        self.snapper = snapper
        self.services = get_services(self.config)

    def _update_image_hashes(self, env: Env):
        for key in list(env.keys()): # Dict size will change, hence copy env.keys into a list
            if key.startswith("SERVICE_") and key.endswith("_IMAGE_TAGGED"):
                entry_name = key.removeprefix("SERVICE_").removesuffix("_IMAGE_TAGGED")
                image_tagged = env[key]

                # Check for environment variables in the tagged image (${VAR} format)
                import re
                def replace_env_vars(s: str, vars: dict[str, str]):
                    def replace_var(match: re.Match) -> str:
                        var_name: str = match.group(1)
                        fallback: str = match.group(0)
                        return vars.get(var_name, fallback)

                    pattern = r'\${([A-Za-z0-9_]+)}'
                    return re.sub(pattern, replace_var, s)

                # Apply environment variable substitution
                interpolated_image = replace_env_vars(image_tagged, env)
                if interpolated_image != image_tagged:
                    log.verbose(f"Interpolated image name: {image_tagged} → {interpolated_image}")
                    image_tagged = interpolated_image

                log.verbose(
                    f"Found tagged image entry for \"{entry_name}\": "
                    f"{image_tagged}"
                )

                current_hash = env.get(
                    "_".join(["SERVICE", entry_name, "IMAGE", "HASHED"]),
                    None
                )
                if current_hash is None:
                    log.verbose(
                        f"There's no hashed image reference for \"{entry_name}\""
                        f" in {self.config['ENV_FILE_NAME']} currently"
                    )
                else:
                    log.verbose(
                        "The current hashed image reference for "
                        f"\"{entry_name}\" is: {current_hash}")

                new_hash = self.resolver.resolve_image_version(image_tagged)

                if new_hash == current_hash:
                    log(f"{entry_name}: {image_tagged} stays at {current_hash}")
                else:
                    env[
                        "_".join(["SERVICE", entry_name, "IMAGE", "HASHED"])
                    ] = new_hash
                    log(
                        f"{colors.Green}{entry_name}: {image_tagged} is "
                        f"now at {new_hash}{colors.Reset}"
                    )

    def _check_permission_compose_tool(self, folder: Path, svc_name: str) -> bool:
        log(f"Ensuring permission for \"{self.config['COMPOSE_TOOL']}\"..")
        ret = subprocess.run(
            self.config["COMPOSE_TOOL"].split(" ") + ["ps"],
            cwd=folder,
            capture_output=True
        ).returncode
        if ret != 0:
            log.error(
                f"Cannot update service \"{svc_name}\", because "
                f"cannot use \"{self.config['COMPOSE_TOOL']}\" (returncode {ret})"
            )
            return False
        return True

    def _cater_for_snapshot(self, folder: Path, svc_name: str) -> bool:
        if self.config["SERVICE_SNAPSHOT"]:
            log(f"Taking a snapshot of {folder} using snapper..")
            try:
                self.snapper.snapshot_folder(
                    folder,
                    message=f"Update container images {str(datetime.today())}"
                )
            except Exception as e:
                log.error(
                    f"Cannot update service \"{svc_name}\", because "
                    f"snapshotting failed: {e}"
                )
                return False
        return True

    def _cater_for_updating_env_file(self, env: Env, svc_name: str) -> bool:
        log(f"Writing updated {env.path} configuration..")
        try:
            env.write()
        except Exception as e:
            log.error(
                f"Cannot update service \"{svc_name}\", because "
                f"writing .env file failed: {e}"
            )
            return False
        return True

    def _cater_for_image_pull(self, folder: Path, svc_name: str) -> bool:
        if self.config["SERVICE_PULL"]:
            log(f"pulling images for service \"{svc_name}\"..")
            ret = subprocess.run(
                self.config["COMPOSE_TOOL"].split(" ") + ["pull"],
                cwd=folder
            ).returncode
            if ret != 0:
                log.error(
                    f"Cannot update service \"{svc_name}\", because "
                    f"pulling images failed (returncode {ret})"
                )
                return False
        return True

    def _cater_for_restart(self, folder: Path, svc_name: str) -> bool:
        if self.config["SERVICE_STOP_START"]:
            if self.config["STOP_START_METHOD"] == "compose":
                log(f"stopping service \"{svc_name}\"..")
                ret = subprocess.run(
                    self.config["COMPOSE_TOOL"].split(" ") + ["down"],
                    cwd=folder
                ).returncode
                if ret != 0:
                    log.error(
                        f"Failed to stop service \"{svc_name}\" (returncode {ret})"
                    )
                    return False

                log(f"Starting \"{svc_name}\" service..")
                ret = subprocess.run(
                    self.config["COMPOSE_TOOL"].split(" ") + ["up", "-d"],
                    cwd=folder
                ).returncode
                if ret != 0:
                    log.error(
                        f"Failed to start service \"{svc_name}\" (returncode {ret})"
                    )
                    return False
            elif self.config["STOP_START_METHOD"] in ["systemd-system", "systemd-user"]:
                systemd_service = f"{self.config['COMPOSE_TOOL']}@{svc_name}"
                log(
                    f"Restarting {self.config['STOP_START_METHOD'].replace('-',' ')} service {systemd_service}"
                )
                cmdlist = ["systemctl"]
                if "-user" in self.config["STOP_START_METHOD"]:
                    cmdlist.append("--user")
                cmdlist += ["restart", systemd_service]
                ret = subprocess.run(cmdlist, cwd=folder).returncode
                if ret != 0:
                    log.error(
                        f"Failed to restart service \"{svc_name}\" (returncode {ret})"
                    )
                    return False
            else:
                log.error(
                    f"Failed to restart service \"{svc_name}\". Unknown method '{self.config['STOP_START_METHOD']}'"
                )
                return False
        return True


    def update_service(self, folder: Path) -> exit_code.Exit_Code | None:
        svc_name = folder.stem  # Only the folder name itself, not the whole path
        log(f"Working on service \"{svc_name}\"", highlight=True)

        env_file = folder / self.config["ENV_FILE_NAME"]
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
            log(f"Changes pending for \"{svc_name}\"")
        else:
            log(f"No changes for \"{svc_name}\", done.")
            return

        if not self._check_permission_compose_tool(folder, svc_name):
            return exit_code.TOOL_ERROR

        if not self._cater_for_snapshot(folder, svc_name):
            return exit_code.SNAPSHOT_ERROR

        if not self._cater_for_updating_env_file(env, svc_name):
            return exit_code.ENV_ERROR

        if not self._cater_for_image_pull(folder, svc_name):
            return exit_code.IMAGE_PULL_ERROR

        if not self._cater_for_restart(folder, svc_name):
            return exit_code.SERVICE_RESTART_ERROR

    def update_all_services(self) -> list[exit_code.Exit_Code]:
        errors: list[exit_code.Exit_Code] = []
        for svc in self.services:
            e = self.update_service(svc)
            if e is not None:
                errors.append(e)
        return errors
