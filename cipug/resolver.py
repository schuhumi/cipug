import json
import subprocess
import time
from dataclasses import dataclass
from typing import Any

from cipug.typing import JsonDictType, ensure_type

from .config import Config
from .log import log


@dataclass
class CacheEntry:
    time: float
    result: str


class Image_Version_Resolver:
    """Uses skopeo to resolve container tags like ":latest" to their respective
    hashed tag. It also caches results to not hit docker-hubs restrictive
    rate limit so quickly."""

    def __init__(self):
        config = Config()
        self.cache_file = config["CACHE_LOCATION"]
        self.cache_duration = config["CACHE_DURATION"]
        self.cache: dict[str, CacheEntry] = {}
        log.vverbose(f"Image-Version-Resolver cache file is set to {self.cache_file}")
        if self.cache_file.is_file(): # A cache file exists already
            # due to isinstance() in ensure_type() we can only pass it a un-parametrized generic here.
            # That again doesn't make the linter happy...
            j: JsonDictType = ensure_type(  # type: ignore[reportUnknownVariableType]
                json.loads(self.cache_file.read_text()),
                dict,
                "Outer structure of cache needs to be dict"
            )
            for name, properties in j.items():
                p: dict[str, Any] = ensure_type( # type: ignore[reportUnknownVariableType]
                    properties,
                    dict,
                    "First level values of cache need to be dicts"
                )
                n: str = ensure_type(name, str)
                self.cache[n] = CacheEntry(
                    time=ensure_type(
                        p["time"],
                        float,
                        "Time value for cache entry needs to be float"
                    ),
                    result=ensure_type(
                        p["result"],
                        str,
                        "Result value for cache entry needs to be string"
                    )
                )

    def write_cache(self):
        self.cache_file.write_text(json.dumps(
            {
                name: {
                    "time": entry.time,
                    "result": entry.result
                } for name, entry in self.cache.items()
            },
            sort_keys=True,
            indent=4
        ))

    def resolve_image_version(self, name: str) -> str:
        # name is what gets plugged into "image: ..." in a compose file,
        # for example: "ghcr.io/paperless-ngx/paperless-ngx:latest"
        current_time = time.time()
        if name in self.cache:
            # There's a chache entry
            entry = self.cache[name]
            age = current_time-entry.time
            if age <= self.cache_duration:
                # And young enough -> use it
                log.vverbose(
                    f"Resolved {name} to {entry.result} (cached {int(age)}s ago)"
                )
                return entry.result
            else:
                log.vverbose(f"Cache entry for {name} expired")

        # If there's no cache entry, or it is incomplete, or too old:
        info = json.loads(
            subprocess.check_output(["skopeo", "inspect", "--no-tags", "docker://"+name])
        )
        result = f'{info["Name"]}@{info["Digest"]}'

        # Populate the cache
        if name not in self.cache:
            self.cache[name] = CacheEntry(time=current_time, result=result)
        self.write_cache()

        log.vverbose(f"Resolved {name} to {result} (by looking up remote)")
        # The result will look something like:
        # "ghcr.io/paperless-ngx/paperless-ngx@sha256:1a603fd...."
        return result
