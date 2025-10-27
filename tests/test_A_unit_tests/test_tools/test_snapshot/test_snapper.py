from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cipug.service import Service
from cipug.tools.snapshot import Snapper
from tests.mock_tools import Snapper as SnapperMock
from tests.mock_tools.environment import Environment, LogEntry


def test_snapper():
    # When instantiating cipug.snapper.Snapper, it reads the existing configs using the
    # snapper command line tool. Using the tests.mock_tools.environment.Environment, we
    # make cipug call a mockup of a snapper tool, that we know the output of
    # (see tests/mock_tools/tools/snapper.py). This way, we can test that
    # cipug.snapper.Snapper does what it is supposed to do.
    tmp_ctx = TemporaryDirectory()
    tmp_path = Path(tmp_ctx.name)
    test_services = tmp_path / "services"
    service_example = test_services / "immich"
    service_example.mkdir(parents=True)
    with Environment(
        tools=[SnapperMock],
        env_overwrites={
            "MOCK_TOOL_SNAPPER_ENV_CONF": str(service_example),  # Add our service example to the snapper mock tool
            "CIPUG_SNAPSHOTS_DIR_SNAPPER": ".snapshots"  # for testing snapper.get_last_snapshot_date()
        },
        tmp_ctx=tmp_ctx,  # reuse the temporary directory for the environment
    ) as e:
        snapper = Snapper()  # queries snapper command line tool for configs
        # We now expect one call to the mockup snapper command line tool
        log: list[LogEntry] = e.log
        assert len(log) == 1
        entry = log[0]
        assert entry.name == "snapper"
        assert entry.action.returncode == 0
        assert len(snapper.configs) == 3  # 2 hardcoded + 1 from MOCK_TOOL_SNAPPER_ENV_CONF

        # So far we expect that no snapshots exist
        service = Service(service_example)
        assert snapper.get_last_snapshot_date(service) is None

        # We now simulate snapshotting a folder with the mockup snapper command line tool
        # (for the path value see tests/mock_tools/tools/snapper.py)
        t_before_snapshot = datetime.now()
        snapper.create_snapshot(service, "testmessage")
        t_after_snapshot = datetime.now()

        log = e.log
        assert len(log) == 2  # Another call to snapper was made
        entry = log[1]
        assert entry.name == "snapper"
        assert entry.action.returncode == 0
        assert entry.argv[1:] == [
            "-c",
            "envconf",
            "create",
            "--description",
            "testmessage",
        ]

        # Test if retrieving the snapshot datetime works correctly
        t_snapshot: datetime | None = snapper.get_last_snapshot_date(service)
        assert t_snapshot is not None
        assert t_before_snapshot <= t_snapshot <= t_after_snapshot

        # Simulate snapshotting something that doesn't exist
        with pytest.raises(Exception):
            snapper.create_snapshot(Service(Path("/this/does/not/exist")), "testmessage")
