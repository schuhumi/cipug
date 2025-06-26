import subprocess

from .log import log
from .config import Config

def check_dependencies(config: Config):
    """Check if the required utilities can be run"""

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
            log.error(f"Could not find tool \"{tool}\", cannot proceed.", exit_code=3)


def prune_images(config: Config):
    if config["PRUNE_IMAGES"]:
        log("Pruning images..")
        ret = subprocess.run(
            config["CONTAINER_TOOL"].split(" ") + ["image", "prune", "-f"]
        ).returncode
        if ret != 0:
            log.error(
                f"Failed to prune images (returncode {ret})"
            )
