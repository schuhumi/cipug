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


def main():
    if len(sys.argv) > 1:
        log.error(
            "cipug does not support parameters. Please use environment "
            "variables instead. exiting.",
            exit_code = 1
        )
    config = Config()
    check_dependencies(config)
    prune_images(config)
    resolver = Image_Version_Resolver(config)
    snapper = Snapper()
    updater = Updater(config=config, resolver=resolver, snapper=snapper)
    updater.update_all_services()
