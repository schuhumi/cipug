#!/usr/bin/env python3

"""
Welcome to cipug, the container images pinning and updating gadget.
"""

import subprocess
import os
import glob
import sys
import json
import time
import copy
from tempfile import gettempdir
from pathlib import Path
from datetime import datetime


class colors:
    # Escape sequences for colorful text in the terminal
    Reset = "\033[0m"

    Bold       = "\033[1m"
    Dim        = "\033[2m"
    Underlined = "\033[4m"
    Blink      = "\033[5m"
    Reverse    = "\033[7m"
    Hidden     = "\033[8m"

    ResetBold       = "\033[21m"
    ResetDim        = "\033[22m"
    ResetUnderlined = "\033[24m"
    ResetBlink      = "\033[25m"
    ResetReverse    = "\033[27m"
    ResetHidden     = "\033[28m"

    Default      = "\033[39m"
    Black        = "\033[30m"
    Red          = "\033[31m"
    Green        = "\033[32m"
    Yellow       = "\033[33m"
    Blue         = "\033[34m"
    Magenta      = "\033[35m"
    Cyan         = "\033[36m"
    LightGray    = "\033[37m"
    DarkGray     = "\033[90m"
    LightRed     = "\033[91m"
    LightGreen   = "\033[92m"
    LightYellow  = "\033[93m"
    LightBlue    = "\033[94m"
    LightMagenta = "\033[95m"
    LightCyan    = "\033[96m"
    White        = "\033[97m"

    BackgroundDefault      = "\033[49m"
    BackgroundBlack        = "\033[40m"
    BackgroundRed          = "\033[41m"
    BackgroundGreen        = "\033[42m"
    BackgroundYellow       = "\033[43m"
    BackgroundBlue         = "\033[44m"
    BackgroundMagenta      = "\033[45m"
    BackgroundCyan         = "\033[46m"
    BackgroundLightGray    = "\033[47m"
    BackgroundDarkGray     = "\033[100m"
    BackgroundLightRed     = "\033[101m"
    BackgroundLightGreen   = "\033[102m"
    BackgroundLightYellow  = "\033[103m"
    BackgroundLightBlue    = "\033[104m"
    BackgroundLightMagenta = "\033[105m"
    BackgroundLightCyan    = "\033[106m"
    BackgroundWhite        = "\033[107m"


class log():
    """Simple logging functionality, use:
    log("message") for normal output
    log.error("message", exit_code) for errors on stderr with optional exiting
    log.[v]verbose("message") for [very] verbose logs
    """
    verbosity=1 # default, gets overwritten in Config.load_from_env()
    
    def __new__(cls, msg: str, verbosity: int = 1, highlight: bool = False):
        if cls.verbosity>=verbosity:
            if highlight:
                print(f"{colors.Yellow}{msg}{colors.Reset}")
                return
            print(msg)

    @classmethod
    def error(cls, msg: str, exit_code: int = 0):
        print(f"{colors.Bold}{colors.Red}{msg}{colors.Reset}", file=sys.stderr)
        if exit_code>0:
            sys.exit(exit_code)
    
    @classmethod
    def verbose(cls, msg: str):
        cls(f"{colors.Dim}{msg}{colors.Reset}", verbosity=2)
    
    @classmethod
    def vverbose(cls, msg: str):
        cls(f"{colors.Dim}{msg}{colors.Reset}", verbosity=3)


class Config(dict):
    """Get config for cipug from environment variables. This has
    nothing to do with the .env file for compose."""
    def __init__(self):
    
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
        
        unset = object()  # Flag that there is no default -> variable is required
        settings_schema = {
            "VERBOSITY": (1, int),
            "SERVICES_ROOT": (unset, Path),
            "COMPOSE_TOOL": ("podman-compose", str),
            "SERVICE_STOP_START": ("true", Str2Bool),
            "SERVICE_SNAPSHOT": ("true", Str2Bool),
            "COMPOSE_FILE_NAME": ("compose.yml", str),
            "ENV_FILE_NAME": (".env", str),
            "CACHE_DURATION": (60*60, int),
            "CACHE_LOCATION": (Path(gettempdir()) / "cipug_cache.json", Path),
            "CONFIG_FILE": ("", str)
        }
        for name, (default, cast_to) in settings_schema.items():
            value = os.environ.get("CIPUG_"+name, default)
            if value is unset:
                # maybe we will get it later in a config file
                self[name] = unset
                continue
            
            try:
                casted_value = cast_to(value)
            except Exception as e:
                log.error(
                    f"Could not interpret environment variable CIPUG_{name}, which "
                    f"is supposed to be of type {cast_to} and set to \"{value}\": {e}",
                    exit_code=4
                )
            self[name] = casted_value
            
        
        if self["CONFIG_FILE"] != "":
            config_path = Path(self["CONFIG_FILE"])
            if not config_path.is_file():
                log.error(f"Could not find config file {config_path}", exit_code=5)
            try:
                config_from_file = json.loads(config_path.read_text())
            except Exception as e:
                log.error(
                    f"Could not read config file {config_path}: {e}",
                    exit_code=5
                )
            if not isinstance(config_from_file, dict):
                log.error(
                    f"Reading json config file {config_path} did not yield a dict, "
                    "but it must be a dict of setting-name and setting-value pairs",
                    exit_code=5
                )
            for name, value in config_from_file.items():
                if name not in settings_schema:
                    log.error(
                        f"Unkown setting {name} in config file {config_path}. "
                        f"Known settings: {', '.join(settings_schema.keys())}",
                        exit_code=5
                    )
                cast_to = settings_schema[name][1]
                try:
                    casted_value = cast_to(value)
                except Exception as e:
                    log.error(
                        f"Could not interpret config settings {name}, "
                        f"which is supposed to be of type {cast_to} "
                        f"and set to \"{value}\": {e}",
                        exit_code=4
                    )
                self[name] = casted_value
        
        # Special handling for verbosity: configure the logging
        log.verbosity = self["VERBOSITY"]
        
        # Check if we have missing settings
        for name in settings_schema.keys():
            if self[name] is unset:
                log.error(
                    f"Setting {name} is required but not set. Please set "
                    f"the CIPUG_{name} environment variable or the {name} "
                    f"setting in a json config file.",
                    exit_code=1
                )
        
        log.verbose(f"Loaded cipug config: \n{'-'*10}\n{self}\n{'-'*10}")
    
    def __str__(self):
        return "\n".join([
            f"CIPUG_{key}={val}" for key, val in self.items()
        ])


def check_dependencies(config: Config):
    """Check if the required utilities can be run"""
    
    tools = ["skopeo"]
    
    if config["SERVICE_STOP_START"]:
        tools.append(config["COMPOSE_TOOL"])
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


class Env(dict):
    """Handle .env files for compose. This includes:
        - loading .env file as dictionary
        - changing entries
        - knowing if any entries where changed
        - writing back to disk
    """
    def __init__(self, path: Path):
        self.path = path  # Remember for writing back to disk
        with open(path, "r") as f:
            # .env file entries can be multiple lines, by adding \ before line ends.
            # If we find such a line, use the following variable to remember which
            # entry to append the next line to.
            key_to_append_next_line_to = None
            for line in f:
                line = line.rstrip("\n")
                if key_to_append_next_line_to is None:
                    # There was no \ at the end of the previous line -> new entry
                    key, val = line.split("=", 1)
                    self[key] = val
                    if line[-1]=="\\":
                        key_to_append_next_line_to = key
                else:
                    # There was a \ at the end of the previous line
                    # -> line belongs to previous key
                    self[key] += "\n" + line
                    if line[-1]!="\\":
                        key_to_append_next_line_to = None
        
        # Remember the the state of the .env on disk. This way we later know
        # whether we need to write updates back to disk
        self.diskstate = {key:copy.copy(val) for key, val in self.items()}
        
        log.vverbose(f"Loaded environment file {path}: \n{'-'*10}\n{self}\n{'-'*10}")
    
    def has_changes(self):
        for key in self.keys():
            if key not in self.diskstate:
                return True
            if self[key] != self.diskstate[key]:
                return True
        for key in self.diskstate.keys():
            if key not in self:
                return True
        return False
    
    def write(self, path: Path | None = None):
        if path is None:
            # No specific location set: write back to where we read it from
            path = self.path
        with open(path, "w") as f:
            f.write("\n".join([
                f"{key}={val}" for key, val in self.items()
            ]))
            self.diskstate = {key:copy.copy(val) for key, val in self.items()}
    
    def __str__(self):
        return "\n".join([
            f"{key}={val}" for key, val in self.items()
        ])


class Image_Version_Resolver():
    """Uses skopeo to resolve container tags like ":latest" to their respective
    hashed tag. It also caches results to not hit docker-hubs restrictive
    rate limit so quickly."""
    
    def __init__(
        self,
        config: Config
    ):
        self.cache_file = config["CACHE_LOCATION"]
        self.cache_duration = config["CACHE_DURATION"]
        self.cache = {}
        log.vverbose(f"Image-Version-Resolver cache file is set to {self.cache_file}")
        if self.cache_file.is_file():
            # A cache file exists already
            self.cache = json.loads(self.cache_file.read_text())
        
    def write_cache(self):
        self.cache_file.write_text(
            json.dumps(self.cache, sort_keys=True, indent=4)
        )
    
    def resolve_image_version(self, name: str):
        # name is what gets plugged into "image: ..." in a compose file,
        # for example: "ghcr.io/paperless-ngx/paperless-ngx:latest"
        current_time = time.time()
        if name in self.cache:
            # There's a chache entry
            if ("time" in self.cache[name]) and ("result" in self.cache[name]):
                # That is complete
                age = current_time-float(self.cache[name]["time"])
                if age <= self.cache_duration:
                    # And young enough -> use it
                    result = self.cache[name]["result"]
                    log.vverbose(
                        f"Resolved {name} to {result} (cached {int(age)}s ago)"
                    )
                    return result
                else:
                    log.vverbose(f"Cache entry for {name} expired")
                    
        # If there's no cache entry, or it is incomplete, or too old:
        info = json.loads(
            subprocess.check_output(["skopeo", "inspect", "docker://"+name])
        )
        result = f'{info["Name"]}@{info["Digest"]}'
        
        # Populate the cache
        if name not in self.cache:
            self.cache[name] = {}
        self.cache[name]["time"] = current_time
        self.cache[name]["result"] = result
        self.write_cache()
        
        log.vverbose(f"Resolved {name} to {result} (by looking up remote)")
        # The result will look something like:
        # "ghcr.io/paperless-ngx/paperless-ngx@sha256:1a603fd...."
        return result


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


class Updater():
    def __init__(
        self,
        config: dict,
        resolver: Image_Version_Resolver,
        snapper: Snapper
    ):
        self.config = config
        self.resolver = resolver
        self.snapper = snapper
        
        if not self.config["SERVICES_ROOT"].is_dir():
            log.error(
                f"CIPUG_SERVICES_ROOT set to {self.config['SERVICES_ROOT']}"
                ", but is not a directory!",
                exit_code=2
            )
        
        pattern = os.path.join("*", config["COMPOSE_FILE_NAME"])
        log.vverbose(
            f"Searching for pattern \"{pattern}\" at {self.config['SERVICES_ROOT']}"
        )
        self.services: list[Path] = []  # list of folders with a compose and env file
        for result in glob.glob(
            pattern,
            root_dir=self.config["SERVICES_ROOT"]
        ):
            compose_file = self.config["SERVICES_ROOT"] / result
            env_file = compose_file.parent / self.config["ENV_FILE_NAME"]
            if not env_file.is_file():
                log.verbose(
                    f"Found {compose_file} but no {env_file}, skipping this folder"
                )
                continue
            self.services.append(compose_file.parent)
        
        if len(self.services)==1:
            log.vebose("Found one service:")
        elif len(self.services)>1:
            log.verbose(f"Found {len(self.services)} services:")
        else:
            log.verbose("Did not find any services.")
        for svc in self.services:
            log.verbose(f" - {svc}")


    def update_service(self, folder: Path):
        svc_name = folder.stem  # Only the folder name itself, not the whole path
        log(f"Working on service \"{svc_name}\"", highlight=True)
        
        env_file = folder / config["ENV_FILE_NAME"]
        if not env_file.is_file():
            log.error(f"File {env_file} not found, cannot update service.")
            return
        env = Env(env_file)
        
        log.vverbose(
            f"Searching {config['ENV_FILE_NAME']} for SERVICE_*_IMAGE_TAGGED "
            "entries that should get resolved to SERVICE_*_IMAGE_HASHED entries."
        )
        # Dict size will change, hence copy env.keys into a list now
        for key in list(env.keys()):  
            match key.split("_"):
                case ["SERVICE", entry_name, "IMAGE", "TAGGED"]:
                    log.verbose(
                        f"Found tagged image entry for \"{entry_name}\": "
                        f"{env[key]}"
                    )

                    current_hash = env.get(
                        "_".join(["SERVICE", entry_name, "IMAGE", "HASHED"]),
                        None
                    )
                    if current_hash is None:
                        log.verbose(
                            f"There's no hashed image reference for \"{entry_name}\""
                            f" in {config['ENV_FILE_NAME']} currently"
                        )
                    else:
                        log.verbose(
                            "The current hashed image reference for "
                            f"\"{entry_name}\" is: {current_hash}")

                    new_hash = self.resolver.resolve_image_version(env[key])
                    
                    if new_hash == current_hash:
                        log(f"{entry_name}: {env[key]} stays at {current_hash}")
                    else:
                        env[
                            "_".join(["SERVICE", entry_name, "IMAGE", "HASHED"])
                        ] = new_hash
                        log(
                            f"{colors.Green}{entry_name}: {env[key]} is "
                            f"now at {new_hash}{colors.Reset}"
                        )

        if not env.has_changes():
            log(f"No changes for \"{svc_name}\", done.")
            return
        
        log(f"Changes pending for \"{svc_name}\"")
        
        if config["SERVICE_STOP_START"]:
            log(f"stopping service \"{svc_name}\"..")
            ret = subprocess.run(
                [config["COMPOSE_TOOL"], "down"],
                cwd=folder
            ).returncode
            if ret != 0:
                log.error(
                    f"Cannot update service \"{svc_name}\", because "
                    f"stopping it failed (returncode {ret})"
                )
                return
                
        if config["SERVICE_SNAPSHOT"]:
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
                return
        
        log(f"Writing updated {env_file} configuration..")
        try:
            env.write()
        except Exception as e:
            log.error(
                f"Cannot update service \"{svc_name}\", because "
                f"writing .env file failed: {e}"
            )
            return
        
        if config["SERVICE_STOP_START"]:
            log(f"Starting \"{svc_name}\" service..")
            ret = subprocess.run(
                [config["COMPOSE_TOOL"], "up", "-d"],
                cwd=folder
            ).returncode
            if ret != 0:
                log.error(
                    f"Failed to start service \"{svc_name}\" (returncode {ret})"
                )
                return
    
    def update_all_services(self):
        for svc in self.services:
            self.update_service(svc)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        log.error(
            "cipug does not support parameters. Please use environment "   
            "variables instead. exiting.",
            exit_code = 1
        )
    config = Config()
    check_dependencies(config)
    resolver = Image_Version_Resolver(config)
    snapper = Snapper()
    updater = Updater(config=config, resolver=resolver, snapper=snapper)
    updater.update_all_services()
