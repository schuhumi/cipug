from datetime import datetime

from .colors import colors
from .config import Config
from .log import log
from .service import Service
from .tools.snapshot import snapshot_check_tools
from .utils import get_services


class Snapshot_Checker:
    """For checking that recent enough snapshots exist."""
    def __init__(self):
        self.config = Config()
        self.services: list[Service] = get_services()

    def check(self) -> bool:
        log("Configured snapshot checks:")
        for name in snapshot_check_tools.get_names():
            tool_class = snapshot_check_tools.get_by_name(name)
            max_age = self.config[f"SNAPSHOTS_MAX_AGE_{name.upper()}"]
            if getattr(tool_class, "uses_directory", True):
                dir = self.config[f"SNAPSHOTS_DIR_{name.upper()}"]
                log(f" - {name}: directory {dir or None} (max. age: {max_age:.2f}h)")
            else:
                enabled = self.config[f"SNAPSHOTS_ENABLE_{name.upper()}"]
                log(f" - {name}: enabled {enabled} (max. age: {max_age:.2f}h)")
        log("Checking for most recent snapshots of services:", highlight=True)
        snapshots_ok = True
        now = datetime.now()
        for service in self.services:
            log(f' - service "{service.name}":')
            for tool in snapshot_check_tools.tools:
                if getattr(tool, "uses_directory", True):
                    if not self.config[f"SNAPSHOTS_DIR_{tool.name.upper()}"]:
                        continue
                else:
                    if not self.config[f"SNAPSHOTS_ENABLE_{tool.name.upper()}"]:
                        continue
                date: datetime | None = tool().get_last_snapshot_date(service)
                max_age: float = self.config[f"SNAPSHOTS_MAX_AGE_{tool.name.upper()}"]

                if isinstance(date, datetime):
                    age_h = (now.timestamp() - date.timestamp()) / 3600
                    log(
                        f"     {tool.name}: {date.isoformat(timespec='seconds')} (age: "
                        f"{colors.Green if age_h <= max_age else colors.Red}{age_h:.2f}h{colors.Reset})"
                    )
                    # Perform age verification
                    if age_h > max_age:
                        snapshots_ok = False
                else:
                    snapshots_ok = False
                    log(f"     {tool.name}: {colors.Red}None{colors.Reset}")
        return snapshots_ok
