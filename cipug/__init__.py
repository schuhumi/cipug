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
    check_dependencies(config)

    if "--check-snapshots" in sys.argv:
        checker = Snapshot_Checker(config)
        if checker.check():
            log("All required snapshots were found.")
        else:
            log.error("Snapshots are missing or too old!", exit_code=exit_code.SNAPSHOTS_NOK)

    if (len(sys.argv) == 1) or ("--update" in sys.argv):
        # No arguments, default update behavior
        prune_images(config)
        resolver = Image_Version_Resolver(config)
        snapper = Snapper()
        updater = Updater(config=config, resolver=resolver, snapper=snapper)
        errors = updater.update_all_services()
        if errors:
            log.error("Encountered errors during updating!", exit_code=errors)
        else:
            log("Updated services successfully")
