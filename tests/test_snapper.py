from pathlib import Path
from cipug.snapper import Snapper
import pytest
from tests.mock_tools.environment import Environment, LogEntry
from tests.mock_tools.tools.snapper import Snapper as SnapperMock


def test_snapper():
    # When instantiating cipug.snapper.Snapper, it reads the existing configs using the
    # snapper command line tool. Using the tests.mock_tools.environment.Environment, we
    # make cipug call a mockup of a snapper tool, that we know the output of
    # (see tests/mock_tools/tools/snapper.py). This way, we can test that
    # cipug.snapper.Snapper does what it is supposed to do.
    with Environment([SnapperMock]) as e:
        snapper = Snapper()  # queries snapper command line tool for configs
        # We now expect one call to the mockup snapper command line tool
        log: list[LogEntry] = e.log
        assert len(log) == 1
        entry = log[0]
        assert entry.name == "snapper"
        # We know these from how the snapper MockTool behaves (tests/mock_tools/tools/snapper.py)
        assert entry.action.returncode == 0
        assert len(snapper.configs) == 2

        # We now simulate snapshotting a folder with the mockup snapper command line tool
        # (for the path value see tests/mock_tools/tools/snapper.py)
        snapper.snapshot_folder(Path("/fake/btrfs/subvolume/1"), "testmessage")

        log = e.log
        assert len(log) == 2  # Another call to snapper was made
        entry = log[1]
        assert entry.name == "snapper"
        assert entry.action.returncode == 0
        assert entry.argv[1:] == [
            "-c",
            "testconf-1",
            "create",
            "--description",
            "testmessage",
        ]

        # Simulate snapshotting something that doesn't exist
        with pytest.raises(Exception):
            snapper.snapshot_folder(Path("/this/does/not/exist"), "testmessage")
