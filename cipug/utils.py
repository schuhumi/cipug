import subprocess
from pathlib import Path
import glob
import os

from .log import log
from .config import Config
from . import exit_code


def get_services() -> list[Path]:
    config = Config()
    if not config["SERVICES_ROOT"].is_dir():
        log.error(
            f"CIPUG_SERVICES_ROOT set to {config['SERVICES_ROOT']}"
            ", but is not a directory!",
            exit_code=exit_code.DIRECTORY_NOT_FOUND
        )

    pattern = os.path.join("*", config["COMPOSE_FILE_NAME"])
    log.vverbose(
        f"Searching for pattern \"{pattern}\" at {config['SERVICES_ROOT']}"
    )

    services: list[Path] = []  # list of folders with a compose and env file
    for result in glob.glob(
        pattern,
        root_dir=config["SERVICES_ROOT"]
    ):
        compose_file = config["SERVICES_ROOT"] / result
        env_file = compose_file.parent / config["ENV_FILE_NAME"]
        if not env_file.is_file():
            log.verbose(
                f"Found {compose_file} but no {env_file}, skipping this folder"
            )
            continue
        services.append(compose_file.parent)

    if config["SERVICES_FILTER"] != "":
        filter = config["SERVICES_FILTER"].split(",")
        log.verbose(f"Filtering services to be one of {filter}")
        services = [
            entry for entry in services if entry.stem in filter
        ]

    if config["SERVICES_FILTER_EXCLUDE"] != "":
        filter = config["SERVICES_FILTER_EXCLUDE"].split(",")
        log.verbose(f"Filtering services to not include any of {filter}")
        services = [
            entry for entry in services if entry.stem not in filter
        ]

    if len(services)==1:
        log.verbose("Found one service:")
    elif len(services)>1:
        log.verbose(f"Found {len(services)} services:")
    else:
        log.verbose("Did not find any services.")
    for svc in services:
        log.verbose(f" - {svc}")
    return services



def check_dependencies():
    """Check if the required utilities can be run"""
    config = Config()
    tools = ["skopeo"]

    if config["SERVICE_STOP_START"]:
        tools.append(config["COMPOSE_TOOL"].split(" ")[0])
    else:
        log.vverbose(
            "Skipping looking for a compose tool, as stopping "
            "and starting of services is disabled"
        )

    if config["SERVICE_SNAPSHOT"]:
        tools.append("snapper")
    else:
        log.vverbose(
            "Skipping looking for snapper, as snapshotting of "
            "services is disabled"
        )

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
            config["CONTAINER_TOOL"].split(" ") + ["image", "prune", "-f"]
        ).returncode
        if ret != 0:
            log.error(
                f"Failed to prune images (returncode {ret})"
            )
