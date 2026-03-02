from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from cipug.service import Service
from cipug.tools.snapshot.zfs import Zfs
from tests.mock_tools import Zfs as ZfsMock
from tests.mock_tools.environment import Environment, LogEntry


def test_zfs_snapshot():
    tmp_ctx = TemporaryDirectory()
    tmp_path = Path(tmp_ctx.name)
    test_services = tmp_path / "services"
    service_example = test_services / "immich"
    service_example.mkdir(parents=True)

    with Environment(
        tools=[ZfsMock],
        tmp_ctx=tmp_ctx
    ) as e:
        tool = Zfs()

        # As compared to snapper the init dost not call anything therefore
        # we call assert_dependencies to have some output in the log
        tool.assert_dependencies()
        # We now expect one call to the mockup zfs command line tool
        log: list[LogEntry] = e.log
        assert len(log) == 1
        assert log[0].name == "zfs"
        assert log[0].argv[1] == "--version"

        # Test snapshot creation
        service = Service(service_example)
        tool.create_snapshot(service, "test message")

        log = e.log
        assert len(log) == 3 # previous 1 + list + snapshot

        # Check list command
        assert log[1].name == "zfs"
        assert log[1].argv[1:] == ["list", "-H", "-o", "name", str(service_example)]

        # Check snapshot command
        assert log[2].name == "zfs"
        assert log[2].argv[1] == "snapshot"
        snapshot_name = log[2].argv[2]
        # Verify format: tank/services/immich@cipug-YYYY-MM-DD-HHMM
        assert snapshot_name.startswith("tank/services/immich@cipug-")

        # Test snapshot with image hash
        image_hash = "1234567890abcdef1234567890abcdef"
        tool.create_snapshot(service, "test message", image_hash=image_hash)

        log = e.log
        assert len(log) == 5 # previous 3 + list + snapshot

        snapshot_name_hash = log[4].argv[2]
        # Verify format with hash: ...@cipug-2024-02-21-1500-1234567890ab
        assert "1234567890ab" in snapshot_name_hash
        assert "sha256:" not in snapshot_name_hash

        # Test get_last_snapshot_date
        last_date = tool.get_last_snapshot_date(service)
        assert last_date is not None
        # Mock returns a timestamp from roughly 30 mins ago (1800s)
        assert abs(last_date.timestamp() - (datetime.now().timestamp() - 1800)) < 10

        # Confirm it used the correct 'zfs list' commands
        log = e.log
        # previous 5 + list dataset + list snapshots
        assert len(log) == 7
        assert log[5].argv[1:] == ["list", "-H", "-o", "name", str(service_example)]
        assert log[6].argv[1:] == [
            "list", "-t", "snapshot", "-H", "-o", "name,creation", "-p", "-d", "1", "tank/services/immich"
        ]

        # Test failure: Path does not exist
        with pytest.raises(Exception) as excinfo:
             tool.create_snapshot(Service(Path("/non/existent/path")), "msg")
        assert "does not exist" in str(excinfo.value)


        # Test failure: ZFS command fails (mock specific path to fail)
        # We need to configure the mock to fail for a specific path if we want to test that.
        # But our current mock is simple.
        # Let's test calling generic exception if subprocess fails
        # (which we can force by passing a path that mock handled as error)
        # The zfs mock handles unknown paths in 'list' with return code 1

        error_path = test_services / "error_service"
        error_path.mkdir()
        # Mock Zfs tool returns error for unknown paths in 'list' command
        with pytest.raises(Exception) as excinfo:
            tool.create_snapshot(Service(error_path), "msg")
        assert "Could not determine ZFS dataset" in str(excinfo.value)
