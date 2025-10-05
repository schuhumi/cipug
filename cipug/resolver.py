import json
import time
import subprocess

from .log import log
from .config import Config

class Image_Version_Resolver():
    """Uses skopeo to resolve container tags like ":latest" to their respective
    hashed tag. It also caches results to not hit docker-hubs restrictive
    rate limit so quickly."""

    def __init__(self):
        config = Config()
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
            subprocess.check_output(["skopeo", "inspect", "--no-tags", "docker://"+name])
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
