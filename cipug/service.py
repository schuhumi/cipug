from pathlib import Path


class Service:
    """Service in the sense of something that runs on the server and shall be updated.
    Like nextcloud, immich, traefik, etc...
    """
    path: Path  # The folder or subvolume where a service lives in
    # (i.e. the path that should be snapshotted when a service is being snapshotted)

    def __init__(self, path: Path):
        self.path = path

    @property
    def name(self) -> str:
        # Only the folder name itself, not the whole path
        return self.path.stem
