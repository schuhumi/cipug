from pathlib import Path
from tempfile import gettempdir
import os
import json

from .log import log
from . import exit_code

unset = object()  # Flag that there is no default -> variable is required
not_supplied = object()  # Flag that a environment variable wasn't supplied

class Str2Bool:
    """Utility to interpret environment strings a boolean config values"""
    def __new__(cls, val: str | bool):
        if isinstance(val, bool):
            return val
        if val.lower() in ['true', '1', 'yes']:
            return True
        if val.lower() in ['false', '0', 'no']:
            return False
        log.error(
            f"Could not interpret \"{val}\" as boolean value. "
            "Valid values: true/false, 0/1, yes/no (not case sensitive)"
        )


class Literally:
    def __init__(self, valid_values: list):
        self._valid_values = valid_values

    def __call__(self, val):
        if val not in self._valid_values:
            log.error(
                f"Invalid value {repr(val)}, valid options are: {self._valid_values}",
                exit_code = exit_code.VALUE_ERROR
            )
        return val


class Config(dict):
    """Get config for cipug from environment variables. This has
    nothing to do with the .env file for compose."""
    settings_schema = {
        "VERBOSITY": (1, int),
        "SERVICES_ROOT": (unset, Path),
        "SERVICES_FILTER": ("", str),
        "SERVICES_FILTER_EXCLUDE": ("", str),
        "COMPOSE_TOOL": ("podman-compose", str),
        "CONTAINER_TOOL": ("podman", str),
        "SERVICE_STOP_START": ("true", Str2Bool),
        "STOP_START_METHOD": ("compose", Literally(["compose", "systemd-system", "systemd-user"])),
        "SERVICE_SNAPSHOT": ("true", Str2Bool),
        "SERVICE_PULL": ("true", Str2Bool),
        "PRUNE_IMAGES": ("true", Str2Bool),
        "COMPOSE_FILE_NAME": ("compose.yml", str),
        "ENV_FILE_NAME": (".env", str),
        "CACHE_DURATION": (60*60, int),
        "CACHE_LOCATION": (Path(gettempdir()) / "cipug_cache.json", Path),
        "SNAPSHOTS_DIR_SNAPPER": ("", str),
        "SNAPSHOTS_MAX_AGE_SNAPPER": (1.5, float),
        "SNAPSHOTS_DIR_BTRBK": ("", str),
        "SNAPSHOTS_MAX_AGE_BTRBK": (36, float),
        "CONFIG_FILE": ("", str)
    }

    def _load_config_file(self):
        if self["CONFIG_FILE"] != "":
            config_path = Path(self["CONFIG_FILE"])
            log.verbose(f"Loading config file: {config_path.resolve()}")
            if not config_path.is_file():
                log.error(f"Could not find config file {config_path}", exit_code=exit_code.FILE_NOT_FOUND)
            try:
                config_from_file = json.loads(config_path.read_text())
            except Exception as e:
                log.error(
                    f"Could not read config file {config_path}: {e}",
                    exit_code=exit_code.UNKNOWN_FILE_FORMAT
                )
            if not isinstance(config_from_file, dict):
                log.error(
                    f"Reading json config file {config_path} did not yield a dict, "
                    "but it must be a dict of setting-name and setting-value pairs",
                    exit_code=exit_code.UNKOWN_DATA_STRUCTURE
                )
            for name, value in config_from_file.items():
                if name == "CONFIG_FILE":
                    log.error(
                        "Specifying the config file path inside the config file doesn't make sense.",
                        exit_code=exit_code.VALUE_ERROR
                    )
                if name not in self.settings_schema:
                    log.error(
                        f"Unkown setting {name} in config file {config_path}. "
                        f"Known settings: {', '.join(self.settings_schema.keys())}",
                        exit_code=exit_code.VALUE_ERROR
                    )
                cast_to = self.settings_schema[name][1]
                try:
                    casted_value = cast_to(value)
                except Exception as e:
                    log.error(
                        f"Could not interpret config settings {name}, "
                        f"which is supposed to be of type {cast_to} "
                        f"and set to \"{value}\": {e}",
                        exit_code=exit_code.TYPE_ERROR
                    )
                self[name] = casted_value

    def __init__(self):

        # Handle config file first by making sure we parse the corresponding environment variable setting first,
        # and then load the config file. All other environment variables are handled after, and therefore overwrite
        # the settings from the config file.
        names = ["CONFIG_FILE"] + [
            key for key in self.settings_schema.keys()
            if key != "CONFIG_FILE"
        ]


        for name in names:
            default, cast_to = self.settings_schema[name]
            value = os.environ.get("CIPUG_"+name, not_supplied)
            if value is not_supplied:
                if name not in self.keys():  # Not yet set by config file -> default
                    self[name] = default
                continue

            try:
                casted_value = cast_to(value)
            except Exception as e:
                log.error(
                    f"Could not interpret environment variable CIPUG_{name}, which "
                    f"is supposed to be of type {cast_to} and set to \"{value}\": {e}",
                    exit_code=exit_code.TYPE_ERROR
                )
            self[name] = casted_value
            if name == "CONFIG_FILE":
                self._load_config_file()

        # Special handling for verbosity: configure the logging
        log.verbosity = self["VERBOSITY"]

        # Check if we have missing settings
        for name in self.settings_schema.keys():
            if self[name] is unset:
                log.error(
                    f"Setting {name} is required but not set. Please set "
                    f"the CIPUG_{name} environment variable or the {name} "
                    f"setting in a json config file.",
                    exit_code=exit_code.VALUE_ERROR
                )

        log.verbose(f"Loaded cipug config: \n{'-'*10}\n{self}\n{'-'*10}")

    def __str__(self):
        return "\n".join([
            f"{key}={val}" for key, val in self.items()
        ])
