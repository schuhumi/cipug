import subprocess

from cipug.tools.version_modifier.base import VersionModifierTool

from . import exit_code
from .config import Config
from .log import log
from .service import Service


def get_services(vmt_cls: type[VersionModifierTool]) -> list[Service]:
    config = Config()
    if not config["SERVICES_ROOT"].is_dir():
        log.error(
            f"CIPUG_SERVICES_ROOT set to {config['SERVICES_ROOT']}"
            ", but is not a directory!",
            exit_code=exit_code.DIRECTORY_NOT_FOUND
        )

    services: list[Service] = []
    for subdir in config["SERVICES_ROOT"].iterdir():
        if not subdir.is_dir():
            continue
        if vmt_cls.check_if_folder_is_service(subdir):
            services.append(Service(subdir))

    if config["SERVICES_FILTER"] != "":
        filter = config["SERVICES_FILTER"].split(",")
        log.verbose(f"Filtering services to be one of {filter}")
        services = [
            service for service in services if service.name in filter
        ]

    if config["SERVICES_FILTER_EXCLUDE"] != "":
        filter = config["SERVICES_FILTER_EXCLUDE"].split(",")
        log.verbose(f"Filtering services to not include any of {filter}")
        services = [
            service for service in services if service.name not in filter
        ]

    if len(services)==1:
        log.verbose("Found one service:")
    elif len(services)>1:
        log.verbose(f"Found {len(services)} services:")
    else:
        log.verbose("Did not find any services.")
    for service in services:
        log.verbose(f" - {service}")
    return services


def check_dependencies():
    """Check if the required utilities can be run"""
    tools = ["skopeo"]

    for tool in tools:
        try:
            out = subprocess.check_output([tool, "--version"]).decode("utf-8").strip()
            log.vverbose(f"Found tool: {out}")
        except FileNotFoundError:
            log.error(f"Could not find tool \"{tool}\", cannot proceed.", exit_code=exit_code.SYSTEM_ERROR)


def prune_images():
    config = Config()
    if config["PRUNE_IMAGES"]:
        log("Pruning images..")
        ret = subprocess.run(
            [*config["CONTAINER_TOOL"].split(" "), "image", "prune", "-f"], check=False
        ).returncode
        if ret != 0:
            log.error(
                f"Failed to prune images (returncode {ret})"
            )
