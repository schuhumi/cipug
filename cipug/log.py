import sys
from typing import NoReturn, overload

from .colors import colors
from .exit_code import Exit_Code, MULTIPLE_ERRORS

class log():
    """Simple logging functionality, use:
    log("message") for normal output
    log.error("message", exit_code) for errors on stderr with optional exiting
    log.[v]verbose("message") for [very] verbose logs
    """
    verbosity=1 # default, gets overwritten in Config.load_from_env()

    def __new__(cls, msg: str, verbosity: int = 1, highlight: bool = False):
        if cls.verbosity>=verbosity:
            if highlight:
                print(f"{colors.Yellow}{msg}{colors.Reset}")
                return
            print(msg)

    @classmethod
    @overload
    def error(cls, msg: str):
        ...

    @classmethod
    @overload
    def error(cls, msg: str, exit_code: Exit_Code | list[Exit_Code]) -> NoReturn:
        ...

    @classmethod
    def error(cls, msg: str, exit_code: Exit_Code | list[Exit_Code] |  None = None) -> NoReturn | None:
        if isinstance(exit_code, Exit_Code):
            msg = f"[{exit_code.code}={exit_code.name}] " + msg
        elif isinstance(exit_code, list):
            msg = "[" + ",".join(f"{e.code}={e.name}" for e in exit_code) + "] " + msg

        print(f"{colors.Bold}{colors.Red}{msg}{colors.Reset}", file=sys.stderr)
        if exit_code is not None:
            if isinstance(exit_code, list):
                if len(set(exit_code)) == 1:
                    sys.exit(exit_code.pop().code)
                else:
                    sys.exit(MULTIPLE_ERRORS.code)
            sys.exit(exit_code.code)

    @classmethod
    def verbose(cls, msg: str):
        cls(f"{colors.Dim}{msg}{colors.Reset}", verbosity=2)

    @classmethod
    def vverbose(cls, msg: str):
        cls(f"{colors.Dim}{msg}{colors.Reset}", verbosity=3)
