import json
import os
import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

logfile_env = "MOCK_TOOLS_LOGFILE"


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
        try:
            self.log_path: str = os.environ[logfile_env]
        except KeyError:
            raise RuntimeError(
                f"Environment variable {logfile_env} for jsonl style logfile is required!"
            )

    @abstractmethod
    def run(self, argv: list[str]) -> Action:
        # process arguments and return returncode
        ...

    def _call(self):
        argv = sys.argv
        action: Action = self.run(argv)


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
