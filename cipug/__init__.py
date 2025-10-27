#!/usr/bin/env python3

"""
Welcome to cipug, the container images pinning and updating gadget.
"""

import json
import sys
from pathlib import Path
from typing import Any

from . import exit_code
from .config import Config
from .log import log
from .resolver import Image_Version_Resolver
from .snapshot_check import Snapshot_Checker
from .tools.snapshot import SnapshotCreationTool, snapshot_creation_tools
from .updater import Updater
from .utils import check_dependencies, prune_images


def main():
    config = Config()

    if "--print-config" in sys.argv:
        print(config)
        return

    if "--print-config-json" in sys.argv:
        class PosixPathEncoder(json.JSONEncoder):
            def default(self, o: Any):
                if isinstance(o, Path):
                    return str(o.resolve())
                return super().default(o)

        json.dump(config, sys.stdout, indent=4, cls=PosixPathEncoder)
        return

    check_dependencies()

    if "--check-snapshots" in sys.argv:
        checker = Snapshot_Checker()
        if checker.check():
            log("All required snapshots were found.")
        else:
            log.error("Snapshots are missing or too old!", exit_code=exit_code.SNAPSHOTS_NOK)

    if (len(sys.argv) == 1) or ("--update" in sys.argv):
        # No arguments, default update behavior
        prune_images()
        resolver = Image_Version_Resolver()
        snapshot_creation_tool: SnapshotCreationTool = snapshot_creation_tools.get_by_name(config["SNAPSHOT_TOOL"])()
        updater = Updater(resolver=resolver, snapshot_creation_tool=snapshot_creation_tool)
        errors = updater.update_all_services()
        if errors:
            log.error("Encountered errors during updating!", exit_code=errors)
        else:
            log("Updated services successfully")
