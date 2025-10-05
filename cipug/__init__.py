#!/usr/bin/env python3

"""
Welcome to cipug, the container images pinning and updating gadget.
"""

import sys

from .log import log
from .config import Config
from .resolver import Image_Version_Resolver
from .snapper import Snapper
from .updater import Updater
from .utils import check_dependencies, prune_images
from .snapshots import Snapshot_Checker
from . import exit_code

def main():
    config = Config()

    if "--print-config" in sys.argv:
        print(config)
        return

    if "--print-config-json" in sys.argv:
        import json
        from pathlib import Path
        class PosixPathEncoder(json.JSONEncoder):
            def default(self, obj):
                if isinstance(obj, Path):
                    return str(obj.resolve())
                return super().default(obj)

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
        snapper = Snapper()
        updater = Updater(resolver=resolver, snapper=snapper)
        errors = updater.update_all_services()
        if errors:
            log.error("Encountered errors during updating!", exit_code=errors)
        else:
            log("Updated services successfully")
