from datetime import datetime
from pathlib import Path
from subprocess import CompletedProcess
from tempfile import TemporaryDirectory

from cipug.exit_code import SNAPSHOTS_NOK
from cipug.service import Service
from cipug.tools.snapshot import Snapper, Zfs
from tests.helper import call_cipug
from tests.mock_tools import PodmanDashCompose as PodmanDashComposeMock
from tests.mock_tools import Skopeo as SkopeoMock
from tests.mock_tools import Snapper as SnapperMock
from tests.mock_tools import Zfs as ZfsMock
from tests.mock_tools.environment import Environment


def test_snapshot_check():
    """End2End test `cipug --check-snapshots`"""
    tmp_ctx = TemporaryDirectory()
    tmp_path = Path(tmp_ctx.name)
    test_services = tmp_path / "services"
    service_example = test_services / "immich"
    example_env = service_example / ".env"
    example_compose = service_example / "compose.yml"

    with Environment(
        tools = [SnapperMock, SkopeoMock, PodmanDashComposeMock],
        env_overwrites = {
            "MOCK_TOOL_SNAPPER_ENV_CONF": str(service_example),  # Add our service example to the snapper mock tool
            # Set this here already, so that Config() works outside of the cipug call also
            "CIPUG_SERVICES_ROOT": str(test_services),
        },
        tmp_ctx = tmp_ctx  # reuse the temporary directory for the environment
    ):
        service_example.mkdir(parents=True)
        example_compose.touch()
        # The testing .env with a random outdated hash
        example_env.write_text("")

        cipug_env = {
            "CIPUG_SERVICES_ROOT": test_services,
            "CIPUG_COMPOSE_FILE_NAME": "compose.yml",
            "CIPUG_ENV_FILE_NAME": ".env",
            "CIPUG_SNAPSHOTS_DIR_SNAPPER": ".snapshots",
            "CIPUG_COMPOSE_TOOL": "podman-compose"
        }


        # Test 1: Check for snapper snapshots, althouth they don't exist yet
        cp: CompletedProcess[str] = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        print(cp.stdout)
        print(cp.stderr)
        assert cp.returncode == SNAPSHOTS_NOK.code

        # Test 2: Create snapper snapshots and check for their existence
        snapper = Snapper()  # Use existing tooling to conveniently call (Mock-)snapper
        snapper.create_snapshot(service=Service(service_example), vmt=None)
        cp = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        print(cp.stdout)
        print(cp.stderr)
        assert cp.returncode == 0

        # Test 3: Check for btrbk snapshots, althouth they don't exist yet
        cipug_env["CIPUG_SNAPSHOTS_DIR_BTRBK"] = ".snap_btrbk"
        cp = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        print(cp.stdout)
        print(cp.stderr)
        assert cp.returncode == SNAPSHOTS_NOK.code

        # Test 4: Create btrbk snapshots and check for their existence.
        # Create the mock-snapshot manually since there exists not mock-btrbk-tool
        # as btrbk works autonomously (not being called by cipug)
        now: str = datetime.now().strftime("%Y%m%dT%H%M")
        (service_example / ".snap_btrbk" / f"immich.{now}").mkdir(parents=True, exist_ok=True)
        cp = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        print(cp.stdout)
        print(cp.stderr)
        assert cp.returncode == 0


def test_snapshot_check_zfs():
    """End2End test `cipug --check-snapshots` with ZFS"""
    tmp_ctx = TemporaryDirectory()
    tmp_path = Path(tmp_ctx.name)
    test_services = tmp_path / "services"
    service_example = test_services / "immich"
    example_env = service_example / ".env"
    example_compose = service_example / "compose.yml"

    with Environment(
        tools=[ZfsMock, SkopeoMock, PodmanDashComposeMock],
        env_overwrites={
            "MOCK_TOOL_ZFS_ENV_CONF": str(service_example),
            # Set this here already, so that Config() works outside of the cipug call also
            "CIPUG_SERVICES_ROOT": str(test_services),
        },
        tmp_ctx=tmp_ctx
    ):
        service_example.mkdir(parents=True)
        example_compose.touch()
        # The testing .env with a random outdated hash
        example_env.write_text("")

        cipug_env = {
            "CIPUG_SERVICES_ROOT": test_services,
            "CIPUG_COMPOSE_FILE_NAME": "compose.yml",
            "CIPUG_ENV_FILE_NAME": ".env",
            "CIPUG_COMPOSE_TOOL": "podman-compose",
            "CIPUG_SNAPSHOTS_ENABLE_ZFS": "true"
        }

        # Test 1: Check for zfs snapshots, although they don't exist yet
        cp = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        assert cp.returncode == SNAPSHOTS_NOK.code
        assert "Snapshots are missing or too old!" in cp.stderr

        # Test 2: Create zfs snapshots and check for their existence
        zfs = Zfs()
        zfs.create_snapshot(service=Service(service_example), vmt=None)
        cp = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        assert cp.returncode == 0
        assert "All required snapshots were found." in cp.stdout

        # Test 3: Test with very strict age limit (1 sec), it should fail
        cipug_env["CIPUG_SNAPSHOTS_MAX_AGE_ZFS"] = "0.001"
        cp = call_cipug(
            env=cipug_env,
            args=["--check-snapshots"]
        )
        assert cp.returncode == SNAPSHOTS_NOK.code
        assert "Snapshots are missing or too old!" in cp.stderr
