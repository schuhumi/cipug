import os
import subprocess
import sys
from pathlib import Path
from typing import Any

def clean_env() -> dict[str, str]:
    # Remove any existing cipug specific environment variables to not mess with the tests
    return {
        key:val for key, val in os.environ.copy().items()
        if not key.startswith("CIPUG_")
    }

def call_cipug(
    env: dict[str, Any] | None = None,
    args: list[str] | None = None
) -> subprocess.CompletedProcess[str]:
    env_complete = clean_env().copy()
    if env is not None:
        for key, val in env.items():
            env_complete[key] = str(val)
    if args is None:
        args = []
    return subprocess.run(
        [
            sys.executable,  # current Python interpreter
            "-m",
            "cipug"
        ] + args,
        cwd=Path(__file__).resolve().parent.parent,
        env=env_complete,
        capture_output=True,
        text=True
    )
