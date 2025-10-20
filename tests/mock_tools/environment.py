import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

import tests
from tests.mock_tools.tools.base import Action, MockTool, logfile_env


@dataclass
class LogEntry:
    # Every call to a MockTool corresponds to one LogEntry. In the tests, cipug calls one or multiple
    # MockTools once or multiple times. Then the test can verify that cipug did what was expected
    # by looking at the log (list[LogEntry]).
    name: str
    time: float
    argv: list[str]
    action: Action

    @property
    def cmdline(self) -> list[str]:
        return [self.name, *self.argv[1:]]


class Environment:
    # Creates executables for the requested MockTools in a temporary directory, and bends
    # environment variables such that cipug calls the MockTools instead of the real command
    # line tools. Also provides a convenient way to get the log of MockTool calls.
    tools: list[type[MockTool]]
    env_overwrites: dict[str, str | None]  # None means the variable should be deleted
    env_overwrites_backup: dict[str, str | None]
    tmp_ctx: tempfile.TemporaryDirectory[str]
    logfile_path: Path

    def __init__(
        self,
        tools: list[type[MockTool]],
        env_overwrites: dict[str, str | None] | None = None,
        tmp_ctx: tempfile.TemporaryDirectory[str] | None = None
    ):
        self.tools = tools
        self.env_overwrites = env_overwrites or {}
        self.tmp_ctx = tmp_ctx or tempfile.TemporaryDirectory()
        self.logfile_path = Path(self.path).resolve() / "tools_log.jsonl"

    def __enter__(self):
        self.tmp_ctx.__enter__()
        for tool in self.tools:
            self._install_tool(tool)
        self.env_overwrites_backup = {}
        for key, val in self.env_overwrites.items():
            if (val is None) and (key not in os.environ):
                # We want to make sure an environment variable is absent that is already absent
                # -> do nothing
                continue
            self.env_overwrites_backup[key] = os.environ.get(key, None)
            if val is None:
                if key in os.environ:
                    os.environ.pop(key)
                    os.unsetenv(key)
            else:
                val_str = str(val)
                os.environ[key] = val_str
                os.putenv(key, val_str)
        self.os_path_backup = os.environ["PATH"]
        os_paths = os.environ["PATH"].split(os.pathsep)
        if self.path in os_paths:
            raise RuntimeError(
                "Unexpectedly found temporary tools environment in $PATH before setting it up. "
                "Be aware that the mock_tools environment isn't suited for concurrency!"
            )
        os.environ["PATH"] = os.pathsep.join([self.path, *os_paths])
        # Changes in os.environ only effect Python-land. For the underlying C-land to know about
        # the environment variable changes, additional calls to os.putenv() and os.unsetenv() are
        # necessary. (That is important because the subprocesses get spawned in C-land)
        os.putenv("PATH", os.environ["PATH"])
        if logfile_env in os.environ:
            raise RuntimeError(
                "Unexpectedly found MOCK_TOOLS_LOGFILE environment variable before setting it up. "
                "Be aware that the mock_tools environment isn't suited for concurrency!"
            )
        os.environ[logfile_env] = str(self.logfile_path)
        os.putenv(logfile_env, os.environ[logfile_env])
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ):
        os.environ.pop(logfile_env)
        os.unsetenv(logfile_env)
        os.environ["PATH"] = self.os_path_backup
        os.putenv("PATH", os.environ["PATH"])
        for key, val in self.env_overwrites_backup.items():
            if val is None:
                os.environ.pop(key)
                os.unsetenv(key)
            else:
                os.environ[key] = val
                os.putenv(key, val)
        self.tmp_ctx.__exit__(exc_type, exc_val, exc_tb)

    @property
    def path(self) -> str:
        # The directory where the MockTool binaries are in
        return self.tmp_ctx.name

    def _install_tool(self, tool: type[MockTool]):
        dest = Path(self.path) / tool.name  # target binary path
        # The mocktool needs to load the tests.mock_tools module, therefore
        # we need the path to tests for prepending it to PYTHONPATH
        pypath = Path(tests.__file__).resolve().parent
        # The binary is a small python snippet that imports the respective
        # MockTool class from the tests.mock_tools module, makes an instance
        # and calls it. The _call() is handled in tests/mock_tools/tools/base.py.
        # It caters for the logfile as well as calling the call() method of the
        # tool itself, where the decision happens what Action() to take.
        dest.write_text(
            f"""#!/usr/bin/env python3
import sys
sys.path.insert(0, '{pypath!s}')
from {tool.__module__} import {tool.__name__}
t = {tool.__name__}()
t._call()
"""
        )
        # Make executable
        st = os.stat(dest)
        os.chmod(dest, st.st_mode | stat.S_IEXEC)

    @property
    def log(self) -> list[LogEntry]:
        if not self.logfile_path.is_file():
            return []
        log: list[LogEntry] = []
        with open(self.logfile_path) as logf:
            for line in logf:
                jentry = json.loads(line)
                action = Action(
                    returncode=jentry["ret"],
                    stdout=jentry["stdout"],
                    stderr=jentry["stderr"],
                )
                entry = LogEntry(
                    name=jentry["name"],
                    time=jentry["time"],
                    argv=jentry["argv"],
                    action=action,
                )
                log.append(entry)
        return log
