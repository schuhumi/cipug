import json
import subprocess
from pathlib import Path

from .log import log

class Snapper():
    """Interact with the snapper utility. Specifically, it can create snapshots
    of subvolumes specified by volume path. It does that by going through snapper's
    configs and finding out which one belongs to that path. That way, cipug does not
    need to know the respective snapper config names from the user.
    """
    def __init__(self):
        self.configs = json.loads(
            subprocess.check_output(
                ["snapper", "--jsonout", "list-configs"]
            ).decode("utf-8")
        )["configs"]
        log.vverbose(f"Loaded snapper configs: \n{json.dumps(self.configs, indent=2)}")

    def snapshot_folder(self, path: Path, message: str):
        config_name = None
        for each in self.configs:
            subvol = Path(each["subvolume"])
            if subvol.resolve() == path.resolve():
                config_name = each["config"]
                break

        if config_name is None:
            raise KeyError(f"No snapper config found for folder {path}")

        completed_process = subprocess.run([
	        "snapper",
	        "-c",
	        config_name,
	        "create",
	        "--description",
	        message
        ])
        if completed_process.returncode != 0:
            raise Exception(
                f"Failed to snapshot using config {config_name}, "
                f"returncode {completed_process.returncode}."
            )
            # We do not handle any stdout/stderr here, because snapper
            # wrote it there already itself when it ran
