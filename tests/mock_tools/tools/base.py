import os
import sys
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
import time


@dataclass
class Action:
    # When a MockTool is called, it checks the arguments and populates the Action
    # dataclass with what it wants to simulate accordingly.
    returncode: int = 0
    stdout: str | None = None
    stderr: str | None = None


class MockTool(ABC):
    name: str  # the name of the binary

    def __init__(self):
        logfile_env_name = "MOCK_TOOLS_LOGFILE"
        self.log_path: str | None = os.environ.get(logfile_env_name, None)

        if self.log_path is None:
            raise RuntimeError(
                f"Environment variable {logfile_env_name} for jsonl style logfile is required!"
            )

    @abstractmethod
    def run(self, argv: list[str]) -> Action:
        # process arguments and return returncode
        ...

    def _call(self):
        argv = sys.argv
        action: Action = self.run(argv)

        if self.log_path is None:
            raise RuntimeError("log_path not initialized")

        # Write a jsonl-style logfile
        # https://jsonltools.com/what-is-jsonl
        # We do it with jsonl so that we can append in every run
        with open(self.log_path, "a") as log_file:
            log_file.write(
                json.dumps(
                    {
                        "time": time.time(),
                        "name": self.name,
                        "argv": argv,
                        "ret": action.returncode,
                        "stdout": action.stdout,
                        "stderr": action.stderr,
                    }
                )
                + "\n"
            )
        # Execute what the Action says
        if action.stdout is not None:
            sys.stdout.write(action.stdout)
        if action.stderr is not None:
            sys.stderr.write(action.stderr)
        sys.exit(action.returncode)
