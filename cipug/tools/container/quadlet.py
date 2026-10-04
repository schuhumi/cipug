
import os
import subprocess
from pathlib import Path

from cipug import exit_code
from cipug.config import Config
from cipug.log import log
from cipug.service import Service
from cipug.tools.version_modifier.quadlet import ContainerFile, get_quadlet_dir
from cipug.typing import Success

from .base import ContainerTool


class QuadletTool(ContainerTool):
    @classmethod
    def assert_dependencies(cls):
        config = Config()
        cp = subprocess.run(
            [*config["CONTAINER_TOOL"].split(" "), "ps"],
            check=False,
            capture_output=True
        )
        ret = cp.returncode
        if ret != 0:
            print(cp.stdout.decode(), cp.stderr.decode())
            log.error(
                f'Failed to use {config["CONTAINER_TOOL"]}',
                exit_code=exit_code.TOOL_ERROR
            )

        cp = subprocess.run(
            [*config["CONTAINER_TOOL"].split(" "), "quadlet", "list"],
            check=False,
            capture_output=True
        )
        ret = cp.returncode
        if ret != 0:
            print(cp.stdout.decode(), cp.stderr.decode())
            log.error(
                f'Failed to use {config["COMPOSE_TOOL"]}',
                exit_code=exit_code.TOOL_ERROR
            )

    def __init__(self) -> None:
        self.config = Config()

    @staticmethod
    def _is_symlink(path: Path) -> bool:
        # os.readlink() only succeeds for symlinks: regular files,
        # directories and everything else raise an OSError (-> False),
        # so nothing that isn't a symlink itself can pass this check.
        # A symlink whose target is missing still passes (that's the point).
        try:
            os.readlink(path)
        except OSError:
            return False
        return True

    def _remove_symlink(self, path: Path) -> Success:
        # Remove the symlink itself. Path.unlink() on a symlink deletes only
        # the link, never its target. We refuse to touch anything that isn't
        # a symlink, so files and directories can never be deleted here.
        if not self._is_symlink(path):
            log.error(f"Refusing to remove {path}: not a symlink")
            return False
        try:
            path.unlink()
        except OSError as e:
            log.error(f"Failed to remove quadlet symlink {path}: {e}")
            return False
        return True

    def _points_into_service_quadlet_dir(self, link: Path) -> Path | None:
        # The quadlet directory a symlink points to (even when that directory
        # is already gone), or None when the link doesn't point to a service's
        # quadlet dir inside SERVICES_ROOT. The check reads the symlink ITSELF
        # (os.readlink), so it works for dangling links and never follows the
        # link for anything that isn't one.
        config = self.config
        try:
            raw = Path(os.readlink(link))
        except OSError:
            return None
        if not raw.is_absolute():
            raw = link.parent / raw
        raw = raw.resolve()
        if raw.name != config["QUADLET_DIR"] or raw.parent.parent != config["SERVICES_ROOT"].resolve():
            return None
        return raw

    def cleanup(self) -> Success:
        """Tidy up the symlinks in the quadlet install directory that relate
        to services:
          - remove symlinks that point to a quadlet folder which no longer
            exists (e.g. the user got rid of a service)
          - replace symlinks that point to an existing service's quadlet
            folder but don't follow the "<service-name>.units" naming
            convention (renaming them, or dropping them when a correctly
            named link already covers the service)
        Only symlinks are ever removed - never their targets, never
        directories, never regular files."""
        ret: Success = True
        install_dir = self.config["QUADLET_INSTALL_DIR"]
        if not install_dir.is_dir():
            return True
        # rglob matches symlink entries by name but does not descend into
        # symlinked directories, so there is no risk of loops or of
        # operating inside the quadlet folders themselves
        for each in sorted(install_dir.rglob("*.units")):
            target = self._points_into_service_quadlet_dir(each)
            if target is None:
                # Not a symlink (files/dirs fail the readlink check), not
                # named *.units, or doesn't point into a service's quadlet
                # dir -> never touched
                continue
            if not each.exists():
                # Dangling: the service's quadlet dir is gone. Remove the
                # link itself; there is nothing to rename it to anymore.
                log(f"Removing stale quadlet symlink {each} -> {target}")
                ret = self._remove_symlink(each) and ret
                continue
            if not target.is_dir() or not any(target.glob("*.container")):
                # The folder still exists but holds no quadlet units, so this
                # is not (yet) a service cipug manages -> leave it alone
                continue
            expected = install_dir / f"{target.parent.name}.units"
            if each == expected:
                continue  # correctly named link to an existing service quadlet dir
            if self._is_symlink(expected):
                if expected.resolve() != target:
                    log.error(
                        f"Failed to fix quadlet symlink name: expected {expected} "
                        f"points to {expected.resolve()}, not {target}"
                    )
                    ret = False
                    continue
                # A correctly named symlink already exists: the misnamed one
                # is redundant and would generate the units twice.
                log(f"Removing redundant quadlet symlink {each} -> {target} ({expected.name} covers it)")
                ret = self._remove_symlink(each) and ret
                continue
            if expected.exists():
                log.error(f"Failed to fix quadlet symlink name: {expected} exists and is not a symlink")
                ret = False
                continue
            log(f'Repairing quadlet symlink for service "{target.parent.name}": {each} -> {expected}')
            try:
                expected.symlink_to(target)
            except OSError as e:
                log.error(f"Failed to create quadlet symlink {expected}: {e}")
                ret = False
                continue
            ret = self._remove_symlink(each) and ret
        return ret

    def get_units(self, svc: Service) -> list[str]:
        units: list[str] = []
        for each in get_quadlet_dir(svc.path).glob("*.container"):
            cf = ContainerFile(each)
            units.append(cf.container_name)
        return units

    def _cmd(self, svc: Service, cmd: str) -> Success:
        ret = subprocess.run(
            ["systemctl", "--user", cmd, *self.get_units(svc)], check=False
        ).returncode
        if ret != 0:
            log.error(f'Failed to {cmd} service "{svc.name}" (returncode {ret})')
            return False
        return True

    def install(self, svc: Service) -> Success:
        # The quadlet unit files are edited in-place inside the service folder.
        # The systemd user quadlet generator is made to pick them up via a symlink
        # pointing to the service's quadlet directory. Make sure the symlink is
        # in place, then let systemd re-generate the units.
        target = get_quadlet_dir(svc.path).resolve()
        link = Path(self.config["QUADLET_INSTALL_DIR"]) / f"{svc.name}.units"
        if link.is_symlink():
            if link.resolve() != target:
                log.error(
                    f'Failed to install quadlets for "{svc.name}": '
                    f"{link} points to {link.resolve()}, expected {target}"
                )
                return False
        elif link.exists():
            log.error(
                f'Failed to install quadlets for "{svc.name}": '
                f"{link} exists and is not a symlink"
            )
            return False
        else:
            log.verbose(f'Installing quadlets for "{svc.name}": linking {target} to {link}')
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(target)
        cp = subprocess.run(
            ["systemctl", "--user", "daemon-reload"],
            check=False
        )
        ret = cp.returncode
        if ret != 0:
            log.error(f'Failed to reload systemd user units (returncode {ret})')
            return False
        return True

    def start(self, svc: Service) -> Success:
        return self.install(svc) and self._cmd(svc, "start")

    def stop(self, svc: Service) -> Success:
        return self._cmd(svc, "stop")

    def restart(self, svc: Service) -> Success:
        return self.install(svc) and self._cmd(svc, "restart")

    def pull(self, svc: Service) -> Success:
        for each in get_quadlet_dir(svc.path).glob("*.container"):
            cf = ContainerFile(each)
            image_hashed = cf.image_hashed
            if image_hashed is None:
                continue
            cp = subprocess.run(
                [*self.config["CONTAINER_TOOL"].split(" "), "pull", image_hashed],
                check=False
            )
            ret = cp.returncode
            if ret != 0:
                log.error(f'Failed to pull image {image_hashed} (returncode {ret})')
                return False
        return True
