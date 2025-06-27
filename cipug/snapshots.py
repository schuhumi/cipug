from datetime import datetime
from pathlib import Path

from .log import log
from .config import Config
from .utils import get_services
from .colors import colors

class Snapshot_Checker:
    def __init__(self, config: Config):
        self.config = config
        self.services: list[Path] = get_services(config)

    def _last_snapshot_date_snapper(self, svc: Path) -> datetime | None:
        subdir = self.config["SNAPSHOTS_DIR_SNAPPER"]
        if not subdir:
            return None
        dir = svc / subdir
        if not dir.is_dir:
            log.error(f"{dir} is not a folder")

        try:
            latest = sorted(
                dir.glob("*/info.xml"),
                key=lambda p: p.stat().st_ctime,
                reverse=True
            )[0]
        except IndexError:
            # Empty list -> no snapshots
            return None

        return datetime.fromtimestamp(latest.stat().st_ctime)

    def _last_snapshot_date_btrbk(self, svc: Path) -> datetime | None:
        subdir = self.config["SNAPSHOTS_DIR_BTRBK"]
        if not subdir:
            return None
        dir = svc / subdir
        if not dir.is_dir:
            log.error(f"{dir} is not a folder")

        try:
            latest = sorted(
                dir.glob("*.*T*"),
                reverse=True
            )[0]
        except IndexError:
            # Empty list -> no snapshots
            return None

        datestr: str = latest.name.split(".", -1)[1]
        # For example: 20250626T0100
        return datetime.strptime(datestr, "%Y%m%dT%H%M")

    def check(self) -> bool:
        log("Configured relative snapshot locations:")
        for name, dir, max_age in [
            ("snapper", self.config['SNAPSHOTS_DIR_SNAPPER'], self.config["SNAPSHOTS_MAX_AGE_SNAPPER"]),
            ("btrbk", self.config['SNAPSHOTS_DIR_BTRBK'], self.config["SNAPSHOTS_MAX_AGE_BTRBK"])
        ]:
            log(f" - {name}: {dir or None} (max. age: {max_age:.2f}h)")
        log("Checking for most recent snapshots of services:", highlight=True)
        snapshots_ok = True
        now = datetime.now()
        for folder in self.services:
            svc_name: str = folder.stem  # Only the folder name itself, not the whole path
            log(f" - service \"{svc_name}\":")
            kind: str  # Which kind of snapshots
            date: datetime | None
            max_age: float  # in hours
            snapshot_types: list[tuple[str, datetime | None, float]] = []  # (kind, last snap, max age)
            if self.config['SNAPSHOTS_DIR_SNAPPER']:
                snapshot_types.append((
                    "snapper",
                    self._last_snapshot_date_snapper(folder),
                    self.config["SNAPSHOTS_MAX_AGE_SNAPPER"]
                ))
            if self.config['SNAPSHOTS_DIR_BTRBK']:
                snapshot_types.append((
                    "btrbk",
                    self._last_snapshot_date_btrbk(folder),
                    self.config["SNAPSHOTS_MAX_AGE_BTRBK"]
                ))

            for kind, date, max_age in snapshot_types:
                if isinstance(date, datetime):
                    age_h = (now.timestamp() - date.timestamp())/3600
                    log(
                        f"     {kind}: {date.isoformat(timespec='seconds')} (age: "
                        f"{colors.Green if age_h <= max_age else colors.Red}{age_h:.2f}h{colors.Reset})"
                )
                else:
                    snapshots_ok = False
                    log(f"     {kind}: {colors.Red}None{colors.Reset}")
        return snapshots_ok
