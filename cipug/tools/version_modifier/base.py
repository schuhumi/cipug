from abc import ABC, abstractmethod
from dataclasses import dataclass

from cipug.colors import colors
from cipug.log import log
from cipug.resolver import Image_Version_Resolver
from cipug.service import Service
from cipug.tools import Tool


@dataclass
class ContainerVersion:
    resolver: Image_Version_Resolver | None
    name: str  # arbitrary name
    image: str  # docker.io/valkey/valkey
    tag: str  # 8-bookworm
    hash_current: str | None # fea8b3e67b15729d4bb70589eb03367bab9ad1ee89c876f54327fc7c6e618571
    _hash_next: str | None

    @classmethod
    def from_tagged_and_hashed(
        cls,
        resolver: Image_Version_Resolver | None,
        name: str,
        tagged: str,
        hashed: str | None,
    ) -> "ContainerVersion":
        image, tag = tagged.split(":")
        if hashed is None:
            hash_current = None
        else:
            image_h, hash_current = hashed.split("@sha256:")
            if image != image_h:
                # It could be that the tagged version doesn't specify the registry. i.e.
                # "nextcloud:latest"
                # vs.
                # "docker.io/library/nextcloud@sha256:a9ef7ed15dbf3f9fcf6dc2a41a15af572fcc077f220640cabfe574a3ffbf5766"
                if not image_h.endswith(image):
                    raise ValueError(f"image mismatch: {image} != {image_h}")
                else:
                    # Take the more precise image description from the tagged case
                    image = image_h
        return cls(
            resolver=resolver,
            name=name,
            image=image,
            tag=tag,
            hash_current=hash_current,
            _hash_next=None
        )

    @property
    def hash_next(self) -> str:
        if self._hash_next is None:
            if self.resolver is None:
                raise RuntimeError("No resolver spcified, cannot resolve tagged image to hash.")
            hashed_next = self.resolver.resolve_image_version(self.tagged)
            hash_next = hashed_next.split("@sha256:")[-1]
            self._hash_next = hash_next
        return self._hash_next

    @property
    def hashed_current(self) -> str | None:
        # docker.io/valkey/valkey@sha256:fea8b3e67b15729d4bb70589eb03367bab9ad1ee89c876f54327fc7c6e618571
        return f"{self.image}@sha256:{self.hash_current}"

    @property
    def hashed_next(self) -> str:
        return f"{self.image}@sha256:{self.hash_next}"

    @property
    def tagged(self) -> str:
        # docker.io/valkey/valkey:8-bookworm
        return f"{self.image}:{self.tag}"

    def has_update(self, logging: bool = False) -> bool:
        r = self.hash_current != self.hash_next
        if logging:
            if r:
                log(f"{colors.Green}{self.name}: {self.tagged} is now at {self.hash_next}{colors.Reset}")
            else:
                log(f"{self.name}: {self.tagged} stays at {self.hash_current}")
        return r


class VersionModifierTool(Tool, ABC):
    container_versions: list[ContainerVersion]

    @abstractmethod
    def __init__(
        self,
        svc: Service,
        resolver: Image_Version_Resolver,
    ) -> None:
        # Read the container versions from the respective representation and
        # put them in self.containerVersions
        ...

    @abstractmethod
    def _store_next_hashes(self) -> None:
        # Write the hashed_next values in self.containerVersions back into the respective representation
        ...

    def write_hashes(self) -> None:
        self._store_next_hashes()
        for cv in self.container_versions:
            cv.hash_current = cv.hash_next

    def has_updates(self, logging: bool = False) -> bool:
        # !! We need the list() here because we want to run cv.has_update for EVERY cv, not only until we find
        # one that is true!!
        return any(list(cv.has_update(logging) for cv in self.container_versions))

    def get_container_version(self, name:str, case_sensitive: bool = True) -> ContainerVersion | None:
        for cv in self.container_versions:
            if case_sensitive:
                if cv.name == name:
                    return cv
            elif cv.name.lower() == name.lower():
                return cv
        return None
